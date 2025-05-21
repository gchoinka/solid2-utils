import itertools
from typing import Dict, List

from solid2 import cube, translate
from solid2.core.object_base import OpenSCADObject

from solid2_utils import Mod
from solid2_utils.mod import t,s,r


def assert_all_same(result: Dict[str, OpenSCADObject]) -> Dict[str, List[str]]:
    as_scad: Dict[str, str] = {k: v.as_scad() for k, v in result.items()}

    as_scad_reverse: Dict[str, List[str]] = dict()
    for k, v in as_scad.items():
        as_scad_reverse.setdefault(v, []).append(k)

    return as_scad_reverse


def test_mod_single():
    c: OpenSCADObject = cube([10., 10., 10.])
    result: Dict[str, OpenSCADObject] = dict()
    result["member"] = c.translate(10., 0., 0.)
    result["openscad"] = translate(10., 0., 0.)(c)

    result["mod_call"] = Mod().tx(10.)(c)
    result["mod_do"] = Mod().do(tx=10.)(c)
    result["mod_t_x_0"] = Mod().t(x=10.)(c)
    result["mod_t_x_1"] = Mod().t(10.)(c)
    result["mod_t_x_2"] = Mod().t(10.,0.)(c)
    result["mod_t_x_3"] = Mod().t(10.,0.,0.)(c)
    result["mod_t_xyz_0"] = Mod().t(x=10., y=0., z=0.)(c)
    result["mod_t_xyz_1"] = Mod().t(x=10., y=0.)(c)
    result["mod_t_xyz_2"] = Mod().t(x=10.)(c)
    result["mod_t_xyz_3"] = Mod().t(10., 0., 0.)(c)
    result["mod_t_xyz_4"] = Mod().t([10., 0., 0.])(c)
    result["mod_t_xyz_5"] = Mod().t((10., 0., 0.))(c)
    result["mod_t_xyz_6"] = t(x=10.)(c)
    result["mod_t_xyz_7"] = t(x=10.)(c)

    as_scad_reverse = assert_all_same(result)

    for a, b in itertools.pairwise(as_scad_reverse.keys()):
        assert a == b, f"a is {','.join(as_scad_reverse[a])}; b is {','.join(as_scad_reverse[b])}"


def test_mod():
    c: OpenSCADObject = cube([10., 10., 10.])
    result: Dict[str, OpenSCADObject] = dict()
    result["member"] = c.translate(10., 0., 0.).translate(10., 0., 0.).translate(0., -5., 0.)
    result["openscad"] = translate(0., -5., 0.)(translate(10., 0., 0.)(translate(10., 0., 0.)(c)))

    result["mod_init"] = Mod().tx(10.).tx(10.).ty(-5.)(c)
    result["mod_call"] = Mod().tx(10.).tx(10.).ty(-5.)(c)

    result["mod_init_1"] = t(x=10.).tx(10.).ty(-5.)(c)
    result["mod_call_1"] = t(x=10.).tx(10.).ty(-5.)(c)

    pos = t(x=10.).tx(10.).ty(-5.)
    result["mod_save_pos"] = pos(c)

    as_scad_reverse = assert_all_same(result)

    for a, b in itertools.pairwise(as_scad_reverse.keys()):
        assert a == b, f"a is {','.join(as_scad_reverse[a])}; b is {','.join(as_scad_reverse[b])}"


def test_translate_scale_mirror():
    c: OpenSCADObject = cube([5., 5., 5.])
    result: Dict[str, OpenSCADObject] = dict()
    result["member"] = c.translate(10., 0., 0.).scale(10., 1., 1.).mirror(True, False, False)

    result["mod"] = t(x=10.).s(10., 1., 1.).mx()(c)

    as_scad_reverse = assert_all_same(result)

    for a, b in itertools.pairwise(as_scad_reverse.keys()):
        assert a == b, f"a is {','.join(as_scad_reverse[a])}; b is {','.join(as_scad_reverse[b])}"