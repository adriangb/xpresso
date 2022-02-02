from typing import Iterable, Sequence, Tuple, TypeVar

T = TypeVar("T")


def grouped(items: Sequence[T], n: int = 2) -> Iterable[Tuple[T, ...]]:
    """s -> [(s0, s1, s2,...sn-1), (sn, sn+1 , sn+2,...s2n-1), ...]
    list(grouped([1, 2], 2)) == [(1, 2)]
    list(grouped([1, 2, 3, 4], 2)) == [(1, 2), (3, 4)]
    """
    if len(items) % n != 0:
        raise ValueError("items must be equally divisible by n")
    return zip(*[iter(items)] * n)
