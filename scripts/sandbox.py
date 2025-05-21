from __future__ import annotations

from collections.abc import Sequence
from typing import Tuple


class M:

    def __xor__(self, other:int | float| Sequence | Tuple[int|float, int| float, int| float]| Tuple[int|float, int| float]| Tuple[int|float]) -> M:
        return self
    def __rxor__(self, other:int | float| Sequence | Tuple[int|float, int| float, int| float]| Tuple[int|float, int| float]| Tuple[int|float]) -> M:
        return self^other

    def __or__(self, other:M) -> M:

        return self

    def __ror__(self, other: M) -> M:
        return self | other

t = M()
tx = M()
ty = M()
tz = M()

def main() -> None:
    b = 10^tx|5^ty|(5,4,3)^t|(5,4)^t
    pass

if "__main__" == __name__:
    main()