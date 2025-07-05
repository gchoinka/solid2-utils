import hashlib
import logging
import shutil
from functools import partial
from pathlib import Path
from typing import Callable, Iterable, Tuple, Dict, List

from solid2 import import_stl
from solid2.core.object_base import OpenSCADObject

from solid2_utils.render import RenderTask, save_to_file

OpenSCADCacheFN = Callable[[Iterable[Tuple[OpenSCADObject, Path]]], Dict[str, OpenSCADObject]]


def default_no_cache_to_stl(obj_list: Iterable[Tuple[OpenSCADObject, Path]]) -> Dict[str, OpenSCADObject]:
    return {str(key.as_posix()): obj for obj, key in obj_list}


_cache_to_stl = default_no_cache_to_stl


def cache_to_stl(obj_list: Iterable[Tuple[OpenSCADObject, Path]]) -> Dict[str, OpenSCADObject]:
    return _cache_to_stl(obj_list)


def set_cache_to_stl_cache_function(cache_fn: OpenSCADCacheFN) -> OpenSCADCacheFN:
    global _cache_to_stl
    old = _cache_to_stl
    _cache_to_stl = cache_fn
    return old


def set_cache_to_stl_setting(openscad_bin: Path, cache_dir: Path) -> OpenSCADCacheFN:
    cache_fn = partial(cache_to_stl_advanced, openscad_bin=openscad_bin, build_dir=cache_dir)
    return set_cache_to_stl_cache_function(cache_fn)


def cache_to_stl_advanced(obj_list: Iterable[Tuple[OpenSCADObject, Path]], build_dir: Path, openscad_bin: Path) -> Dict[
    str, OpenSCADObject]:
    rts_all = [RenderTask(obj, build_dir.joinpath(name)) for obj, name in obj_list]
    rts_filtered: List[RenderTask] = list()
    for n in range(len(rts_all)):
        rts_all[n].filename = Path(
            rts_all[n].filename.as_posix() + "_" + hashlib.md5(rts_all[n].scad_object.as_scad().encode()).hexdigest())
        if not rts_all[n].filename.with_suffix(".stl").exists():
            rts_filtered.append(rts_all[n])
        else:
            logging.info(f"Found {rts_all[n].filename} im cache")

    for rts in rts_filtered:
        filename = rts.filename.as_posix()[:-32]
        for suffix in (".stl", ".scad"):
            filename_last = Path(filename + "last").with_suffix(suffix)
            if filename_last.exists():
                filename_last.unlink()
            try:
                filename_last.symlink_to(rts.filename.with_suffix(suffix))
            except OSError as ex:
                shutil.copy(rts.filename.with_suffix(suffix), filename_last)
    if len(rts_filtered) > 0:
        save_to_file(openscad_bin, rts_filtered, file_types=[".stl"])
    return {str(r.filename.stem[:-33]): import_stl(r.filename.with_suffix(".stl")) for r in rts_all}
