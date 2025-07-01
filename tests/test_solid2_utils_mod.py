import itertools
from typing import Dict, List

from solid2 import cube, translate
from solid2.core.object_base import OpenSCADObject

from solid2_utils.mod import t, Mod, tx


def convert_to_scad(result: Dict[str, OpenSCADObject]) -> Dict[str, List[str]]:
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

    result["mod_call"] = tx(10.)(c)
    result["mod_t_x_0"] = t(x=10.)(c)
    result["mod_t_x_1"] = t(10.)(c)
    result["mod_t_x_2"] = t(10., 0.)(c)
    result["mod_t_x_3"] = t(10., 0., 0.)(c)
    result["mod_t_xyz_0"] = t(x=10., y=0., z=0.)(c)
    result["mod_t_xyz_1"] = t(x=10., y=0.)(c)
    result["mod_t_xyz_2"] = t(x=10.)(c)
    result["mod_t_xyz_3"] = t(10., 0., 0.)(c)
    result["mod_t_xyz_4"] = t([10., 0., 0.])(c)
    result["mod_t_xyz_5"] = t((10., 0., 0.))(c)
    result["mod_t_xyz_6"] = t(x=10.)(c)
    result["mod_t_xyz_7"] = t(x=10.)(c)

    as_scad_reverse = convert_to_scad(result)

    for a, b in itertools.pairwise(as_scad_reverse.keys()):
        assert a == b, f"a is {','.join(as_scad_reverse[a])}; b is {','.join(as_scad_reverse[b])}"


def test_mod():
    c: OpenSCADObject = cube([10., 10., 10.])
    result: Dict[str, OpenSCADObject] = dict()
    result["member"] = c.translate(10., 0., 0.).translate(10., 0., 0.).translate(0., -5., 0.)
    result["openscad"] = translate(0., -5., 0.)(translate(10., 0., 0.)(translate(10., 0., 0.)(c)))

    result["mod_init"] = tx(10.).tx(10.).ty(-5.)(c)
    result["mod_call"] = tx(10.).tx(10.).ty(-5.)(c)

    result["mod_init_1"] = t(10.).tx(10.).ty(-5.)(c)
    result["mod_call_1"] = t(x=10.).t(x=10.).ty(-5.)(c)

    pos = t(x=10.).tx(10.).ty(-5.)
    result["mod_save_pos"] = pos(c)

    as_scad_reverse = convert_to_scad(result)

    for a, b in itertools.pairwise(as_scad_reverse.keys()):
        assert a == b, f"a is {','.join(as_scad_reverse[a])}; b is {','.join(as_scad_reverse[b])}"


def test_translate_scale_mirror():
    c: OpenSCADObject = cube([5., 5., 5.])
    result: Dict[str, OpenSCADObject] = dict()
    result["member"] = c.translate(10., 0., 0.).scale(10., 1., 1.).mirror(1, 0, 0)

    result["mod"] = t(x=10.).s(10., 1., 1.).mx()(c)

    as_scad_reverse = convert_to_scad(result)

    for a, b in itertools.pairwise(as_scad_reverse.keys()):
        assert a == b, f"a is {','.join(as_scad_reverse[a])}; b is {','.join(as_scad_reverse[b])}"


def test_enable_disable():
    c: OpenSCADObject = cube([5., 5., 5.])

    new_pos = t(z=5).r(z=45)
    none_pos = Mod()

    enable = False
    result: Dict[str, OpenSCADObject] = dict()

    result["no_mod"] = c
    p = new_pos if enable else none_pos
    result["call_false"] = p(c)
    result["call_disable"] = p(c)

    as_scad_reverse = convert_to_scad(result)

    for a, b in itertools.pairwise(as_scad_reverse.keys()):
        assert a == b, f"a is {','.join(as_scad_reverse[a])}; b is {','.join(as_scad_reverse[b])}"

    enable = True
    p = new_pos if enable else none_pos
    result["call_default_enable"] = new_pos(c)
    result["call_true"] = p(c)

    as_scad: Dict[str, str] = {k: v.as_scad() for k, v in result.items()}

    for key in ("call_default_enable", "call_true"):
        assert as_scad["no_mod"] != as_scad[key]

    for key in ("no_mod", "call_false", "call_disable"):
        result.pop(key, None)

    as_scad_reverse = convert_to_scad(result)
    for a, b in itertools.pairwise(as_scad_reverse.keys()):
        assert a == b, f"a is {','.join(as_scad_reverse[a])}; b is {','.join(as_scad_reverse[b])}"
