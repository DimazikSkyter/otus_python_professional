from domain.unit_of_work import UnitOfWork
from infrastructure.repositories import (
    SqlAlchemyOrderRepository,
    SqlAlchemyProductRepository,
)


class SqlAlchemyUnitOfWork(UnitOfWork):

    def __init__(self, session_factory):
        self.session_factory = session_factory
        self.session = None

    def __enter__(self):
        self.session = self.session_factory()
        self._products = SqlAlchemyProductRepository(self.session)
        self._orders = SqlAlchemyOrderRepository(self.session)

    def __exit__(self, exception_type, exception_value, traceback):
        if exception_type:
            self.rollback()
        else:
            self.commit()
        self.session.close()

    def commit(self):
        self.session.commit()

    def rollback(self):
        self.session.rollback()

    @property
    def products(self):
        return self._products

    @property
    def orders(self):
        return self._orders
