from typing import List

from domain.services import WarehouseService
from fastapi import Depends, FastAPI
from infrastructure.api.schemas import (OrderItemIn, OrderOut, ProductIn,
                                        ProductOut)
from infrastructure.database import DATABASE_URL
from infrastructure.orm import Base
from infrastructure.unit_of_work import SqlAlchemyUnitOfWork
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

app = FastAPI()

engine = create_engine(DATABASE_URL)
SessionFactory = sessionmaker(bind=engine)
Base.metadata.create_all(engine)


def get_service() -> WarehouseService:
    uow = SqlAlchemyUnitOfWork(SessionFactory)
    return WarehouseService(uow)


@app.post("/products", response_model=List[ProductOut])
def create_products(
    products: List[ProductIn], service: WarehouseService = Depends(get_service)
):
    created = []
    for p in products:
        created.append(service.create_product(p.name, p.quantity, p.price))

    return [
        ProductOut(id=prod.id, name=prod.name, quantity=prod.quantity, price=prod.price)
        for prod in created
    ]


@app.post("/order", response_model=OrderOut)
def create_order(
    items: List[OrderItemIn], service: WarehouseService = Depends(get_service)
):
    pairs = [(item.product_name, item.quantity) for item in items]
    order = service.create_order(pairs)

    return OrderOut(
        id=order.id if hasattr(order, "id") else id(order),
        products=[
            ProductOut(id=p.id, name=p.name, quantity=p.quantity, price=p.price)
            for p in order.products
        ],
    )
