import asyncio
from typing import (Any, Callable, ClassVar, Coroutine, Iterable, Literal,
                    LiteralString, Self, TypeAlias, TypedDict, TypeVar, Unpack)


# await
def run_async(x: Coroutine[Any, Any, int]):
    return x


async def demo_coro():
    await asyncio.sleep(5)
    return "Done"


print("Before run_async")  # Runs immediately
result = asyncio.run(demo_coro())  # Blocks for 1 second
print("After run_async")  # Runs only after the coro finishes
print(result)

# callable

SingleStringInput: TypeAlias = Callable[[str], None]


# class-var


class Foo:
    bar: ClassVar[int] = 0
    """Hint: No need to write __init__"""


# decorator
F = TypeVar("F", bound=Callable[..., object])


def decorator(func: F):
    return func


# empty-tuple
def foo(x: tuple[()]):
    pass


# generic
K = TypeVar("K", int, str, float)
T = TypeVar("T", int, str)


def add(a: K, b: K) -> K:
    return a + b


def add2(a: T, b: T) -> T:
    return a + b


# generic2

T2 = TypeVar("T2", int, str)


def add3(a: T2, b: T2) -> T2:
    return a + b


# generic3
T3 = TypeVar("T3", bound=int)


def add4(a: T3) -> T3:
    return a


# instance-var
class Foo2:
    bar: int


# literal
D: TypeAlias = Literal["left", "right"]


def foo2(direction: D):
    pass


# literalstring
def execute_query(sql: LiteralString, parameters: Iterable[str] = ...):
    pass


# self
class Foo3:
    def return_self(self) -> Self:
        return self


# typed-dict
class Student(TypedDict):
    name: str
    age: int
    school: str


# typed-dict2
class SubStudent(TypedDict, total=False):
    school: str


class Student2(SubStudent):
    name: str
    age: int


# typed-dict3
class SubPerson(TypedDict, total=False):
    age: int
    gender: str
    address: str
    email: str


class Person(SubPerson):
    name: str


# unpack
class Person2(TypedDict):
    name: str
    age: int


def foo111(**kwargs: Unpack[Person2]):
    pass
