from __future__ import annotations

import copy
import itertools
from dataclasses import dataclass
from enum import Enum
from typing import List, Tuple, Sequence, Dict, Any, Set

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


class Opt(Enum):
    Disable = 0
    Enable = 1


@dataclass
class Tr:
    coordinates: XYZ = (0., 0., 0.)


@dataclass
class Sc:
    factor: XYZ = (1., 1., 1.)


@dataclass
class Ro:
    angles: XYZ = (0., 0., 0.)


@dataclass
class Mi:
    axis: Tuple[bool, bool, bool] = (False, False, False)


class Mod:
    def __init__(self, opt: Opt = Opt.Enable):
        self._actions: List[Tr | Ro | Mi | Sc] = list()
        self._opt = opt

    def do(self, **kwargs) -> Mod:
        dim = ["x", "y", "z"]
        opts = ["s", "t", "r", "m"]
        allowed: Set[str] = set(o + d for o, d in itertools.product(opts, dim))

        for key, value in kwargs.items():
            if key not in allowed:
                raise ValueError(f"Please use only the allowed operations {allowed}!")
            if key.startswith("t"):
                args = {key[1]: value}
                self.t(**args)
            if key.startswith("r"):
                args = {key[1]: value}
                self.r(**args)
            if key.startswith("m"):
                args = {key[1]: value}
                self.m(**args)
        return self

    def s(self, *factors: XYZ, x: float | None = None, y: float | None = None,
          z: float | None = None, opt: Opt = Opt.Enable):
        if opt is not None and opt == Opt.Disable:
            return self
        if len(factors) == 1 and isinstance(factors[0], tuple | list):
            self._actions.append(Sc(factors[0]))
        elif len(factors) == 3 and all(isinstance(c, float | int) for c in factors):
            self._actions.append(Sc((factors[0], factors[1], factors[2])))
        elif any(c is not None for c in (x, y, z)):
            self._actions.append(Sc([c if c is not None else 1. for c in (x, y, z)]))
        else:
            raise ValueError("Either factors has to be non None or x,y,z have to be not None")
        return self

    def t(self, *coordinates: XYZ | float, x: float | None = None, y: float | None = None,
          z: float | None = None, opt: Opt = Opt.Enable) -> Mod:
        if opt is not None and opt == Opt.Disable:
            return self
        if len(coordinates) == 1 and isinstance(coordinates[0], tuple | list):
            self._actions.append(Tr(coordinates[0]))
        elif len(coordinates) > 0 and all(isinstance(c, float | int) for c in coordinates):
            mat = [0., 0., 0.]
            for i in range(len(coordinates)):
                mat[i] = coordinates[i]
            self._actions.append(Tr(mat))
        elif any(c is not None for c in (x, y, z)):
            self._actions.append(Tr([c if c is not None else 0. for c in (x, y, z)]))
        else:
            raise ValueError("Either coordinates has to be non None or x,y,z have to be not None")
        return self

    def r(self, *angles: XYZ, x: float | None = None, y: float | None = None,
          z: float | None = None, opt: Opt = Opt.Enable) -> Mod:
        if opt is not None and opt == Opt.Disable:
            return self
        if len(angles) == 1 and isinstance(angles[0], tuple | list):
            self._actions.append(Ro(angles[0]))
        elif len(angles) == 3 and all(isinstance(c, float | int) for c in angles):
            self._actions.append(Ro((angles[0], angles[1], angles[2])))
        elif any(c is not None for c in (x, y, z)):
            self._actions.append(Ro([c if c is not None else 0. for c in (x, y, z)]))
        else:
            raise ValueError("Either angles has to be non None or x,y,z have to be not None")
        return self

    def tx(self, x: float | int, opt: Opt = Opt.Enable) -> Mod:
        return self.t(x=x, opt=opt)

    def ty(self, y: float | int, opt: Opt = Opt.Enable) -> Mod:
        return self.t(y=y, opt=opt)

    def tz(self, z: float | int, opt: Opt = Opt.Enable) -> Mod:
        return self.t(z=z, opt=opt)

    def rx(self, x: float | int, opt: Opt = Opt.Enable) -> Mod:
        return self.r(x=x, opt=opt)

    def ry(self, y: float | int, opt: Opt = Opt.Enable) -> Mod:
        return self.r(y=y, opt=opt)

    def rz(self, z: float | int, opt: Opt = Opt.Enable) -> Mod:
        return self.r(z=z, opt=opt)

    def sx(self, x: float | int, opt: Opt = Opt.Enable) -> Mod:
        return self.s(x=x, opt=opt)

    def sy(self, y: float | int, opt: Opt = Opt.Enable) -> Mod:
        return self.s(y=y, opt=opt)

    def sz(self, z: float | int, opt: Opt = Opt.Enable) -> Mod:
        return self.s(z=z, opt=opt)

    def m(self, x: bool = False, y: bool = False, z: bool = False, opt: Opt = Opt.Enable) -> Mod:
        if opt == Opt.Enable:
            self._actions.append(Mi((x, y, z)))
        return self

    def mx(self, opt: Opt = Opt.Enable) -> Mod:
        return self.m(x=True, opt=opt)

    def my(self, opt: Opt = Opt.Enable) -> Mod:
        return self.m(y=True, opt=opt)

    def mz(self, opt: Opt = Opt.Enable) -> Mod:
        return self.m(z=True, opt=opt)

    def __call__(self, openscad_object: OpenSCADObject, *openscad_objects: OpenSCADObject) -> OpenSCADObject | Sequence[
        OpenSCADObject]:
        result: List[OpenSCADObject] = list()
        for obj in [openscad_object, *openscad_objects]:
            if self._opt == Opt.Disable:
                continue
            for action in self._actions:
                if isinstance(action, Tr):
                    obj = obj.translate(action.coordinates)
                elif isinstance(action, Ro):
                    obj = obj.rotate(action.angles)
                elif isinstance(action, Sc):
                    obj = obj.scale(action.factor)
                elif isinstance(action, Mi):
                    obj = obj.mirror(action.axis)
                else:
                    raise ValueError("Unexpected type for action")
            result.append(obj)
        if len(result) == 1:
            return result[0]
        else:
            return result

    @property
    def obj(self) -> OpenSCADObject | Sequence[OpenSCADObject]:
        return self.__call__()

    def __add__(self, other: Mod) -> Mod:
        new_instance = copy.deepcopy(self)
        new_instance += other
        return new_instance

    def __iadd__(self, other: Mod) -> Mod:
        self._actions.extend(other._actions)
        return self


def t(*coordinates: XYZ, x: float | None = None, y: float | None = None,
      z: float | None = None, opt: Opt = Opt.Enable) -> Mod:
    m = Mod()
    return m.t(*coordinates, x=x, y=y, z=z, opt=opt)


def r(*angles: XYZ, x: float | None = None, y: float | None = None,
      z: float | None = None, opt: Opt = Opt.Enable) -> Mod:
    m = Mod()
    return m.r(*angles, x=x, y=y, z=z, opt=opt)


def s(*factors: XYZ, x: float | None = None, y: float | None = None,
      z: float | None = None, opt: Opt = Opt.Enable) -> Mod:
    m = Mod()
    return m.s(*factors, x=x, y=y, z=z, opt=opt)


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
