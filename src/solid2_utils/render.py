import argparse
import logging
import multiprocessing
import os
import re
import shutil
import subprocess
import sys
import time
import zipfile
from dataclasses import dataclass
from itertools import chain, product
from pathlib import Path
from typing import Tuple, Iterable, List

from solid2 import P3
from solid2.core.object_base import OpenSCADObject


@dataclass
class RenderTask:
    scad_object: OpenSCADObject
    filename: Path
    position: P3 = (0., 0., 0.)


@dataclass
class _RenderTaskArgs:
    scad_object: OpenSCADObject
    filename: Path
    file_types:List[str]
    openscad_bin: Path | None = None
    verbose: bool = False


def _render_to_file(task: _RenderTaskArgs) -> Tuple[Path, float]:
    scad_filename = task.filename.with_suffix(".scad").absolute().as_posix()
    task.scad_object.save_as_scad(scad_filename)
    elapsed = 0.0
    manifold = True
    extra_cli_args = ["--backend", "Manifold"] if manifold else []
    if task.openscad_bin is not None:
        out_filenames = tuple(chain.from_iterable(
            product(("-o",), (task.filename.with_suffix(ext).absolute().as_posix() for ext in task.file_types))))
        openscad_cli_args = [task.openscad_bin, *out_filenames, *extra_cli_args, "--colorscheme", "BeforeDawn",
                             scad_filename]
        return_code = None
        try:
            logging.info(f"Running [{",".join(f'"{s}"' for s in openscad_cli_args)}]")
            start = time.time()

            return_code = subprocess.run(openscad_cli_args, capture_output=True)
            return_code.check_returncode()
            elapsed = (time.time() - start)
            if task.filename.with_suffix(".3mf").exists():
                set_model_name(task.filename.with_suffix(".3mf"), task.filename.name)
        except subprocess.CalledProcessError as ex:
            logging.info(f"Saving {scad_filename}")
            logging.error(ex)
            if return_code is not None:
                logging.error(return_code.stdout)
            return task.filename.absolute(), elapsed
        except ValueError as ex:
            logging.error(ex)
            if return_code is not None:
                logging.error(return_code.stdout)
                logging.error(return_code.stderr)
                sys.stdout.buffer.write(return_code.stderr)
    return task.filename.absolute(), elapsed


def set_model_name(filename: Path, name: str) -> None:
    old_filename = filename
    new_filename = filename.with_suffix(".new")
    try:
        with zipfile.ZipFile(old_filename) as old:
            with zipfile.ZipFile(new_filename, "w") as new:
                for zip_info in old.infolist():
                    not_a_bad_file = zip_info.filename != "3D/3dmodel.model"
                    if not_a_bad_file:
                        new.writestr(zip_info, old.read(zip_info))
                    else:
                        text = old.read("3D/3dmodel.model").decode("utf-8")
                        xml_str = text.replace("OpenSCAD Model", name)
                        with new.open("3D/3dmodel.model", "w", ) as f:
                            f.write(xml_str.encode("utf-8"))
    except zipfile.BadZipFile as exc:
        raise ValueError(f"for file {old_filename}") from exc
    shutil.move(new_filename, old_filename)


def save_to_file(openscad_bin: Path | None, render_tasks: Iterable[RenderTask], file_types:List[str] | None= None,
                 include_filter_regex: re.Pattern[str] | None = None, remove_duplicates=True,
                 verbose: bool = False) -> None:
    if verbose:
        from multiprocessing.dummy import Pool
    else:
        from multiprocessing import Pool

    render_tasks_list = list(render_tasks)
    if remove_duplicates:
        unique_scads_idx = {filename: idx for filename, idx in
                            zip((r.filename for r in render_tasks), range(len(render_tasks_list)))}
        render_tasks_list = [render_tasks_list[idx] for idx in unique_scads_idx.values()]

    file_types = [".3mf", ".png"] if file_types is None else file_types

    render_tasks_args: List[_RenderTaskArgs] = [_RenderTaskArgs(t.scad_object, t.filename, file_types=file_types, openscad_bin=openscad_bin, verbose=verbose) for t in render_tasks_list]
    if include_filter_regex is not None:
        render_tasks_args = [t for t in render_tasks_args if include_filter_regex.search(t.filename.as_posix())]

    logging.info(f"Will generate {", ".join(task.filename.as_posix() for task in render_tasks_args)}", )

    with Pool(max(multiprocessing.cpu_count() - 2, 1)) as pool:
        for filename, elapsed in pool.map(_render_to_file, render_tasks_args):
            logging.info(f"Saved in {elapsed:.2f}s {filename.absolute().as_posix()}")


def solid2_utils_cli(prog: str, description: str, default_output_path: Path):
    parser = argparse.ArgumentParser(prog=prog, description=description)
    parser.add_argument('--skip_rendering', action='store_true')
    parser.add_argument('--preview', action='store_true')
    parser.add_argument('--verbose', action='store_true')
    parser.add_argument('--openscad_bin', type=str)
    parser.add_argument('--include_filter_regex', type=str)
    parser.add_argument('--build_dir', type=str)

    args, unknown_args = parser.parse_known_args()

    output_path = default_output_path if args.build_dir is None else Path(args.build_dir)
    if not os.path.exists(output_path):
        os.makedirs(output_path)

    if args.openscad_bin is not None:
        openscad_bin: Path | None = Path(args.openscad_bin)
    else:
        p = shutil.which("openscad")
        openscad_bin: Path | None = Path(p) if p is not None else None
    if openscad_bin is None and not args.skip_rendering:
        logging.warn("Didn't found openscad in PATH environment variable, skipping rendering 3mf/stl/png!")
        if Path("C:/Program Files/Openscad/openscad.exe").exists():
            openscad_bin = Path("C:/Program Files/Openscad/openscad.exe").absolute()
            logging.warn(f"Found openscad in default folder {openscad_bin.absolute()}")

    return args, output_path, openscad_bin, unknown_args
