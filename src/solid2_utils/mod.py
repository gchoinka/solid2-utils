from __future__ import annotations

import copy
from dataclasses import dataclass
from typing import List, Tuple, Sequence, Dict, Any

from solid2 import P2, P3, P4
from solid2.core.object_base import OpenSCADObject

XYZ = P4 | P3 | P2 | Sequence[float | int] | int | float


def mod_p3(v: XYZ, x: float | int | None = None, y: float | int | None = None, z: float | int | None = None,
           ax: float | int = 0., ay: float | int = 0., az: float | int = 0., mx: float | int = 1., my: float | int = 1.,
           mz: float | int = 1., a: Tuple[float | int, float | int, float | int] | float | int = 0.,
           m: Tuple[float | int, float | int, float | int] | float | int = 1., ) -> P3:
    set_values: Tuple[float, float, float] = (
        float(x) if x is not None else v[0], float(y) if y is not None else v[1], float(z) if z is not None else v[2])
    _a: Tuple[float, float, float] = (float(a[0]), float(a[1]), float(a[2])) if isinstance(a, tuple) else (
        float(a), float(a), float(a))
    _m: Tuple[float, float, float] = (float(m[0]), float(m[1]), float(m[2])) if isinstance(m, tuple) else (
        float(m), float(m), float(m))
    add_values = (ax + _a[0], ay + _a[1], az + _a[2])
    mul_values = (mx * _m[0], my * _m[1], mz * _m[2])
    new_v: List[float] = [vv for vv in v]

    for i in range(3):
        new_v[i] = set_values[i]
        new_v[i] += add_values[i]
        new_v[i] *= mul_values[i]

    return new_v[0], new_v[1], new_v[2]


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


class Mod:
    def __init__(self):
        self._actions: List[_Tr | _Ro | _Mi | _Sc] = list()

    def s(self, *factors: XYZ, x: float | None = None, y: float | None = None,
          z: float | None = None):
        if len(factors) == 1 and isinstance(factors[0], tuple | list):
            self._actions.append(_Sc(factors[0]))
        elif len(factors) == 3 and all(isinstance(c, float | int) for c in factors):
            self._actions.append(_Sc((factors[0], factors[1], factors[2])))
        elif any(c is not None for c in (x, y, z)):
            self._actions.append(_Sc([c if c is not None else 1. for c in (x, y, z)]))
        else:
            raise ValueError("Either factors has to be non None or x,y,z have to be not None")
        return self

    def t(self, *coordinates: XYZ | float, x: float | None = None, y: float | None = None,
          z: float | None = None) -> Mod:
        if len(coordinates) == 1 and isinstance(coordinates[0], tuple | list):
            self._actions.append(_Tr(coordinates[0]))
        elif len(coordinates) > 0 and all(isinstance(c, float | int) for c in coordinates):
            mat = [0., 0., 0.]
            for i in range(len(coordinates)):
                mat[i] = coordinates[i]
            self._actions.append(_Tr(mat))
        elif any(c is not None for c in (x, y, z)):
            self._actions.append(_Tr([c if c is not None else 0. for c in (x, y, z)]))
        else:
            raise ValueError("Either coordinates has to be non None or x,y,z have to be not None")
        return self

    def r(self, *angles: XYZ, x: float | None = None, y: float | None = None,
          z: float | None = None) -> Mod:
        if len(angles) == 1 and isinstance(angles[0], tuple | list):
            self._actions.append(_Ro(angles[0]))
        elif len(angles) == 3 and all(isinstance(c, float | int) for c in angles):
            self._actions.append(_Ro((angles[0], angles[1], angles[2])))
        elif any(c is not None for c in (x, y, z)):
            self._actions.append(_Ro([c if c is not None else 0. for c in (x, y, z)]))
        else:
            raise ValueError("Either angles has to be non None or x,y,z have to be not None")
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

    def m(self, x: int = 0, y: int = 0, z: int = 0) -> Mod:
        self._actions.append(_Mi((x, y, z)))
        return self

    def mx(self) -> Mod:
        return self.m(x=1)

    def my(self) -> Mod:
        return self.m(y=1)

    def mz(self) -> Mod:
        return self.m(z=1)

    def __call__(self, openscad_object: OpenSCADObject, *openscad_objects: OpenSCADObject) -> OpenSCADObject | Sequence[
        OpenSCADObject]:
        result: List[OpenSCADObject] = list()
        for obj in [openscad_object, *openscad_objects]:
            for action in self._actions:
                if isinstance(action, _Tr):
                    obj = obj.translate(action.coordinates)
                elif isinstance(action, _Ro):
                    obj = obj.rotate(action.angles)
                elif isinstance(action, _Sc):
                    obj = obj.scale(action.factor)
                elif isinstance(action, _Mi):
                    obj = obj.mirror(action.axis)
                else:
                    raise ValueError("Unexpected type for action")
            result.append(obj)
        if len(result) == 1:
            return result[0]
        else:
            return result

    def __add__(self, other: Mod) -> Mod:
        new_instance = copy.deepcopy(self)
        new_instance += other
        return new_instance

    def __iadd__(self, other: Mod) -> Mod:
        self._actions.extend(other._actions)
        return self


def t(*coordinates: XYZ, x: float | None = None, y: float | None = None,
      z: float | None = None) -> Mod:
    obj = Mod()
    return obj.t(*coordinates, x=x, y=y, z=z)


def tx(x: float) -> Mod:
    return t(x=x)


def ty(y: float) -> Mod:
    return t(y=y)


def tz(z: float) -> Mod:
    return t(z=z)


def r(*angles: XYZ, x: float | None = None, y: float | None = None,
      z: float | None = None) -> Mod:
    obj = Mod()
    return obj.r(*angles, x=x, y=y, z=z)


def rx(x: float) -> Mod:
    return r(x=x)


def ry(y: float) -> Mod:
    return r(y=y)


def rz(z: float) -> Mod:
    return r(z=z)


def s(*factors: XYZ, x: float | None = None, y: float | None = None,
      z: float | None = None) -> Mod:
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


class LocatedObj:

    def __init__(self, objf, obj_args: List[Any], obj_kwargs: Dict[Any, Any], size: XYZ, pos: Mod | None = None):
        self.obj = objf(*obj_args, **obj_kwargs)
        self.pos = pos
        self.size = size

    def __getitem__(self, index: int) -> float:
        return self.size[index]

    @property
    def x(self) -> float:
        return self.size[0]

    @x.setter
    def x(self, val: float) -> None:
        self.size = mod_p3(self.size, x=val)

    @property
    def y(self) -> float:
        return self.size[1]

    @y.setter
    def y(self, val: float) -> None:
        self.size = mod_p3(self.size, y=val)

    @property
    def z(self) -> float:
        return self.size[2]

    @z.setter
    def z(self, val: float) -> None:
        self.size = mod_p3(self.size, z=val)

    def __add__(self, other) -> OpenSCADObject:
        if isinstance(other, OpenSCADObject):
            return self.obj + other
        elif isinstance(other, LocatedObj):
            return self.obj + other.obj
        else:
            raise ValueError("Plus OP only implemented for OpenSCADObject or LocatedObj")

    def __sub__(self, other) -> OpenSCADObject:
        if isinstance(other, OpenSCADObject):
            return self.obj - other
        elif isinstance(other, LocatedObj):
            return self.obj - other.obj
        else:
            raise ValueError("Minus OP only implemented for OpenSCADObject or LocatedObj")
