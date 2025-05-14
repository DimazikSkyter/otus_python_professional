from typing import (Any, AnyStr, Dict, Final, List, Optional, Tuple, TypeAlias,
                    TypeVar, Union)


def basic_any(x: Any):
    return x


def basic_dict(x: Dict[str, str]):
    return x


# final
my_list: Final[List] = []


def basic_kwargs(**kwargs: Union[str, int]) -> dict[str, Union[str, int]]:
    return kwargs


def basic_list(x: List[str]):
    return x


def basic_optional(x: Optional[int] = None):
    return x


def basic_parameter(x: int):
    return x


def basic_return() -> int:
    return 1


def basic_tuple(x: Tuple[str, int]):
    pass


# typealias
Vector: TypeAlias = List[float]


def basic_union(x: Union[str, int]):
    return x


# variable
a: int
