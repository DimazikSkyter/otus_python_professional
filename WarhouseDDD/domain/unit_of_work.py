from abc import ABC, abstractmethod

from domain.repositories import OrderRepository, ProductRepository


class UnitOfWork(ABC):

    @property
    @abstractmethod
    def products(self) -> ProductRepository:
        pass

    @property
    @abstractmethod
    def orders(self) -> OrderRepository:
        pass

    @abstractmethod
    def __enter__(self):
        pass

    @abstractmethod
    def __exit__(self, exception_type, exception_value, traceback):
        pass

    @abstractmethod
    def commit(self):
        pass

    @abstractmethod
    def rollback(self):
        pass
