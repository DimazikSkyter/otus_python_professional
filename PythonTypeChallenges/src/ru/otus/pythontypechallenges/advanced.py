from array import array
from functools import wraps
from typing import (Any, Callable, Generator, Generic, List, Literal, Never,
                    Protocol, Self, Tuple, TypeVar, Union, cast, overload)


# buffer
class HasBuffer(Protocol):
    def __buffer__(self, flags: int) -> memoryview: ...


BufferLike = Union[bytes, bytearray, memoryview, array, HasBuffer]


def read_buffer(b: BufferLike): ...


# callable-protocol
class SingleStringInput(Protocol):
    def __call__(self, name: str) -> None: ...


# decorator
F = TypeVar("F", bound=Callable[..., None])


def decorator(message: str) -> Callable[[F], F]:
    def wrapper(func: F) -> F:
        @wraps(func)
        def inner(*args, **kwargs):
            return func(*args, **kwargs)

        return cast(F, inner)

    return wrapper


class Descriptor:
    @overload
    def __get__(self, instance: None, owner: type) -> Self:
        """you don't need to implement this"""
        return self

    @overload
    def __get__(self, instance: Any, owner: type) -> str:
        """you don't need to implement this"""
        return str(instance)

    def __get__(self, instance: Any, owner: type) -> Self | str:
        """you don't need to implement this"""
        return str(instance)  # mypy


# forward
class MyClass:
    def __init__(self, x: int) -> None:
        self.x = x

    # TODO: Fix the type hints of `copy` to make it type check
    def copy(self) -> "MyClass":
        copied_object = MyClass(x=self.x)
        return copied_object


# generator
def gen() -> Generator[int, str, None]:
    """You don't need to implement it"""
    yield 1


# generic class
T = TypeVar("T")


class Stack(Generic[T]):
    def __init__(self) -> None:
        self.items: List[T] = []

    def push(self, item: T) -> None:
        self.items.append(item)

    def pop(self) -> T:
        return self.items.pop()


# never
def never_call_me(arg: Never):
    raise RuntimeError("no way")


# never2
def stop() -> Never:
    raise RuntimeError("no way")


# overload
@overload
def process(response: bytes) -> str: ...
@overload
def process(response: int) -> Tuple[int, str]: ...
@overload
def process(response: None) -> None: ...


def process(response: int | bytes | None) -> str | None | tuple[int, str]:
    if isinstance(response, bytes):
        return response.decode()
    elif isinstance(response, int):
        return response, str(response)
    elif response is None:
        return None
    raise TypeError("Unsupported type")


# overload-literal
T_foo = TypeVar("T_foo")


@overload
def foo(value: str, flag: Literal[1]) -> int: ...
@overload
def foo(value: int, flag: Literal[2]) -> str: ...
@overload
def foo(value: Any, flag: Literal[3]) -> List[Any]: ...


# mypy error
# @overload
# def foo(value: T_foo, flag: Any) -> T_foo: ...


def foo(value: Any, flag: Any) -> Any:
    if flag == 1:
        return int(value)
    elif flag == 2:
        return str(value)
    elif flag == 3:
        return list(value)
    elif flag == "4":
        return TypeError("Unsupported type")
    raise TypeError("Unsupported type")
