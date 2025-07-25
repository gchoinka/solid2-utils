import argparse
import functools
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
from typing import Tuple, Iterable, List, Generator

from solid2 import P3, scad_inline, union
from solid2.core.object_base import OpenSCADObject


@dataclass
class RenderTask:
    scad_object: OpenSCADObject
    filename: os.PathLike[str]
    position: P3 = (0., 0., 0.)


def set_output_dir(output_path: Path, render_task: Iterable[RenderTask]) -> Generator[RenderTask, None, None]:
    for rt in render_task:
        yield RenderTask(rt.scad_object, output_path.joinpath(rt.filename), rt.position)


def set_render_task_fn(fn: int, render_task: Iterable[RenderTask]) -> Generator[RenderTask, None, None]:
    for rt in render_task:
        yield RenderTask(union()(scad_inline(f"$fn={fn};\n"), rt.scad_object), rt.filename, rt.position)


@dataclass
class _RenderTaskArgs:
    scad_object: OpenSCADObject
    filename: Path
    file_types: List[str]
    openscad_bin: str | None = None
    verbose: bool = False


def _wslpath(path: str | Path, convert: bool = False) -> str:
    if not convert:
        return path
    if isinstance(path, Path):
        path = str(path.absolute().as_posix())
    to_run = ["wsl", "wslpath", path]
    out = subprocess.run(to_run, capture_output=True, check=False).stdout.decode().strip()
    logging.info(f"{to_run=} {out=}")
    return out


def _render_to_file(task: _RenderTaskArgs) -> Tuple[Path, float]:
    fix_path = functools.partial(_wslpath, convert=task.openscad_bin.startswith("wsl") if task.openscad_bin is not None else False)
    scad_filename = task.filename.with_suffix(".scad").absolute().as_posix()
    task.scad_object.save_as_scad(scad_filename)
    elapsed = 0.0
    manifold = True
    extra_cli_args = ["--backend", "Manifold"] if manifold else []
    if task.openscad_bin is not None:
        out_filenames = tuple(chain.from_iterable(product(("-o",), (
            fix_path(task.filename.with_suffix(ext).absolute().as_posix()) for ext in task.file_types))))
        openscad_bin: List[str] = [task.openscad_bin]
        if task.openscad_bin.startswith("wsl"):
            openscad_bin = task.openscad_bin.split(" ", 1)

        openscad_cli_args = [*openscad_bin, *out_filenames, *extra_cli_args, "--colorscheme", "BeforeDawn",
                             fix_path(scad_filename)]
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


def save_to_file(openscad_bin: str | None, render_tasks: Iterable[RenderTask], file_types: List[str] | None = None,
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

    render_tasks_args: List[_RenderTaskArgs] = [
        _RenderTaskArgs(t.scad_object, Path(t.filename), file_types=file_types, openscad_bin=openscad_bin,
                        verbose=verbose) for t in render_tasks_list]
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

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    output_path = default_output_path if args.build_dir is None else Path(args.build_dir)
    if not os.path.exists(output_path):
        logging.info(f'Output dir "{output_path}" did not exist, trying to create it now')
        os.makedirs(output_path)

    openscad_bin_candidates = [args.openscad_bin, shutil.which("openscad-nightly"), shutil.which("openscad"), ]
    is_wsl = shutil.which("wsl")
    if is_wsl is not None and len(is_wsl) > 0:
        for c in ("openscad-nightly", "openscad"):
            f = subprocess.run(["wsl", "bash", "-l", "-c", f"which {c}"], capture_output=True,
                               check=False).stdout.decode().strip()
            if len(f) > 0:
                openscad_bin_candidates.append(f"wsl {f}")

    openscad_bin: str | None = next((p for p in openscad_bin_candidates if p is not None), None)

    if openscad_bin is None and not args.skip_rendering:
        logging.warn("Didn't found openscad in PATH environment variable, skipping rendering 3mf/stl/png!")

    return args, output_path, openscad_bin, unknown_args
