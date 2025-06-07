from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from domain.services import WarehouseService
from infrastructure.database import DATABASE_URL
from infrastructure.orm import Base
from infrastructure.repositories import (
    SqlAlchemyOrderRepository,
    SqlAlchemyProductRepository,
)
from infrastructure.unit_of_work import SqlAlchemyUnitOfWork

engine = create_engine(DATABASE_URL)
SessionFactory = sessionmaker(bind=engine)
Base.metadata.create_all(engine)


def main():
    uow = SqlAlchemyUnitOfWork(SessionFactory)
    warehouse_service = WarehouseService(uow)
    new_product = warehouse_service.create_product(name="test1", quantity=1, price=100)
    print(f"create product: {new_product}")
    # todo add some actions


if __name__ == "__main__":
    main()
