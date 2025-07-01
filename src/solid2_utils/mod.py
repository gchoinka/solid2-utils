from __future__ import annotations

import copy
from dataclasses import dataclass
from typing import List, Tuple, Sequence

from solid2 import P2, P3, P4
from solid2.core.object_base import OpenSCADObject

XYZ = P4 | P3 | P2 | Sequence[float | int] | int | float


def mod_p3(v: P3, setx: float | int | None = None, sety: float | int | None = None, setz: float | int | None = None,
           addx: float | int = 0., addy: float | int = 0., addz: float | int = 0., mulx: float | int = 1.,
           muly: float | int = 1., mulz: float | int = 1.,
           add: Tuple[float | int, float | int, float | int] | float | int = 0.,
           mul: Tuple[float | int, float | int, float | int] | float | int = 1., ) -> P3:
    set_values: Tuple[float, float, float] = (float(setx) if setx is not None else v[0],
                                              float(sety) if sety is not None else v[1],
                                              float(setz) if setz is not None else v[2])
    _a: Tuple[float, float, float] = (float(add[0]), float(add[1]), float(add[2])) if isinstance(add, tuple) else (
        float(add), float(add), float(add))
    _m: Tuple[float, float, float] = (float(mul[0]), float(mul[1]), float(mul[2])) if isinstance(mul, tuple) else (
        float(mul), float(mul), float(mul))
    add_values = (addx + _a[0], addy + _a[1], addz + _a[2])
    mul_values = (mulx * _m[0], muly * _m[1], mulz * _m[2])
    new_v: List[float] = [vv for vv in v]

    for i in range(3):
        new_v[i] = set_values[i]
        new_v[i] += add_values[i]
        new_v[i] *= mul_values[i]

    return new_v[0], new_v[1], new_v[2]


class _ModP3Action:
    pass


class ModP3:
    def __init__(self, *args: _ModP3Action):
        pass


@dataclass
class _Tr:
    coordinates: XYZ = (0., 0., 0.)


@dataclass
class _Sc:
    factor: XYZ = (1., 1., 1.)


@dataclass
class _Ro:
    angles: XYZ = (0., 0., 0.)


@dataclass
class _Mi:
    axis: Tuple[int, int, int] = (0, 0, 0)


@dataclass
class _Debug:
    flag: bool = True


class Mod:
    def __init__(self):
        self._actions: List[_Tr | _Ro | _Mi | _Sc | _Debug] = list()

    def s(self, *factors: XYZ, x: float | None = None, y: float | None = None, z: float | None = None):
        if len(factors) == 1 and isinstance(factors[0], tuple | list):
            self._actions.append(_Sc(factors[0]))
        elif len(factors) == 1 and isinstance(factors[0], int | float):
            self._actions.append(_Sc((factors[0], factors[0] * 0, factors[0] * 0)))
        elif len(factors) == 2 and isinstance(factors[0], int | float) and isinstance(factors[1], int | float):
            self._actions.append(_Sc((factors[0], factors[1], factors[0] * 0)))
        elif len(factors) == 3 and isinstance(factors[0], int | float) and isinstance(factors[1],
                                                                                      int | float) and isinstance(
            factors[2], int | float):
            self._actions.append(_Sc((factors[0], factors[1], factors[2])))
        elif any(c is not None for c in (x, y, z)):
            self._actions.append(_Sc([c if c is not None else 1. for c in (x, y, z)]))
        else:
            raise ValueError("Either factors has to be non None or x,y,z have to be not None")
        return self

    def t(self, *coordinates: XYZ, x: float | None = None, y: float | None = None, z: float | None = None) -> Mod:
        if len(coordinates) == 1 and isinstance(coordinates[0], tuple | list):
            self._actions.append(_Tr(coordinates[0]))
        elif len(coordinates) == 1 and isinstance(coordinates[0], int | float):
            self._actions.append(_Tr([coordinates[0], coordinates[0] * 0, coordinates[0] * 0]))
        elif len(coordinates) == 2 and isinstance(coordinates[0], int | float) and isinstance(coordinates[1],
                                                                                              int | float):
            self._actions.append(_Tr([coordinates[0], coordinates[1], coordinates[0] * 0]))
        elif len(coordinates) == 3 and isinstance(coordinates[0], int | float) and isinstance(coordinates[1],
                                                                                              int | float) and isinstance(
            coordinates[2], int | float):
            self._actions.append(_Tr([coordinates[0], coordinates[1], coordinates[2]]))
        elif any(c is not None for c in (x, y, z)):
            self._actions.append(_Tr([c if c is not None else 0. for c in (x, y, z)]))
        else:
            raise ValueError("Either coordinates has to be non None or x,y,z have to be not None")
        return self

    def r(self, *angles: XYZ, x: float | None = None, y: float | None = None, z: float | None = None) -> Mod:
        if len(angles) == 1 and isinstance(angles[0], tuple | list):
            self._actions.append(_Ro(angles[0]))
        elif len(angles) == 1 and isinstance(angles[0], int | float):
            self._actions.append(_Ro((angles[0], angles[0] * 0, angles[0] * 0)))
        elif len(angles) == 2 and isinstance(angles[0], int | float) and isinstance(angles[1], int | float):
            self._actions.append(_Ro((angles[0], angles[1], angles[0] * 0)))
        elif len(angles) == 3 and isinstance(angles[0], int | float) and isinstance(angles[1],
                                                                                    int | float) and isinstance(
            angles[2], int | float):
            self._actions.append(_Ro((angles[0], angles[1], angles[2])))
        elif any(c is not None for c in (x, y, z)):
            self._actions.append(_Ro([c if c is not None else 0. for c in (x, y, z)]))
        else:
            raise ValueError("Either angles has to be non None or x,y,z have to be not None")
        return self

    def m(self, x: int = 0, y: int = 0, z: int = 0) -> Mod:
        self._actions.append(_Mi((x, y, z)))
        return self

    def debug(self, flag: bool = True) -> Mod:
        self._actions.append(_Debug(flag))
        return self

    def tx(self, x: float | int) -> Mod:
        return self.t(x=x)

    def ty(self, y: float | int) -> Mod:
        return self.t(y=y)

    def tz(self, z: float | int) -> Mod:
        return self.t(z=z)

    def rx(self, x: float | int) -> Mod:
        return self.r(x=x)

    def ry(self, y: float | int) -> Mod:
        return self.r(y=y)

    def rz(self, z: float | int) -> Mod:
        return self.r(z=z)

    def sx(self, x: float | int) -> Mod:
        return self.s(x=x)

    def sy(self, y: float | int) -> Mod:
        return self.s(y=y)

    def sz(self, z: float | int) -> Mod:
        return self.s(z=z)

    def mx(self) -> Mod:
        return self.m(x=1)

    def my(self) -> Mod:
        return self.m(y=1)

    def mz(self) -> Mod:
        return self.m(z=1)

    def clone(self) -> Mod:
        return copy.deepcopy(self)

    def __call__(self, openscad_object: OpenSCADObject) -> OpenSCADObject:
        for action in self._actions:
            if isinstance(action, _Tr):
                openscad_object = openscad_object.translate(action.coordinates)
            elif isinstance(action, _Ro):
                openscad_object = openscad_object.rotate(action.angles)
            elif isinstance(action, _Sc):
                openscad_object = openscad_object.scale(action.factor)
            elif isinstance(action, _Mi):
                openscad_object = openscad_object.mirror(action.axis)
            elif isinstance(action, _Debug):
                if action.flag:
                    openscad_object = openscad_object.debug()
            else:
                raise ValueError("Unexpected type for action")
        return openscad_object

    def __add__(self, other: Mod) -> Mod:
        new_instance = self.clone()
        new_instance += other
        return new_instance

    def __iadd__(self, other: Mod) -> Mod:
        self._actions.extend(other._actions)
        return self


def t(*coordinates: XYZ, x: float | None = None, y: float | None = None, z: float | None = None) -> Mod:
    obj = Mod()
    return obj.t(*coordinates, x=x, y=y, z=z)


def tx(x: float) -> Mod:
    return t(x=x)


def ty(y: float) -> Mod:
    return t(y=y)


def tz(z: float) -> Mod:
    return t(z=z)


def r(*angles: XYZ, x: float | None = None, y: float | None = None, z: float | None = None) -> Mod:
    obj = Mod()
    return obj.r(*angles, x=x, y=y, z=z)


def rx(x: float) -> Mod:
    return r(x=x)


def ry(y: float) -> Mod:
    return r(y=y)


def rz(z: float) -> Mod:
    return r(z=z)


def s(*factors: XYZ, x: float | None = None, y: float | None = None, z: float | None = None) -> Mod:
    obj = Mod()
    return obj.s(*factors, x=x, y=y, z=z)


def sx(x: float) -> Mod:
    return s(x=x)


def sy(y: float) -> Mod:
    return s(y=y)


def sz(z: float) -> Mod:
    return s(z=z)


def m(x: int = 0, y: int = 0, z: int = 0) -> Mod:
    obj = Mod()
    return obj.m(x=x, y=y, z=z)


def mx() -> Mod:
    return m(x=1)


def my() -> Mod:
    return m(y=1)


def mz() -> Mod:
    return m(z=1)
