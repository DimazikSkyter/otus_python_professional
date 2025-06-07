import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from domain.services import WarehouseService
from infrastructure.orm import Base
from infrastructure.unit_of_work import SqlAlchemyUnitOfWork


@pytest.fixture
def session_factory():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, expire_on_commit=False)


def test_create_product(session_factory):
    name = "Молоко"
    uow = SqlAlchemyUnitOfWork(session_factory)
    service = WarehouseService(uow)

    service.create_product(name, 10, 99.9)

    product = service.find_product_by_name(name)
    assert product.id is not None
    assert product.name == name
    assert product.quantity == 10
    assert product.price == 99.9


def test_create_order(session_factory):
    name1 = "Хлеб"
    name2 = "Сок"
    uow = SqlAlchemyUnitOfWork(session_factory)
    service = WarehouseService(uow)

    service.create_product(name1, 5, 30.0)
    service.create_product(name2, 3, 45.5)

    order = service.create_order([(name1, 2), (name2, 1)])

    assert order is not None
    assert len(order.products) == 2
    assert all(p.id is not None for p in order.products)
