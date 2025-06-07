from typing import List

from sqlalchemy.orm import Session

from domain.models import Order, Product
from domain.repositories import OrderRepository, ProductRepository

from .orm import OrderORM, ProductORM


class SqlAlchemyProductRepository(ProductRepository):
    def __init__(self, session: Session):
        self.session = session

    def add(self, product: Product):
        product_orm = ProductORM(
            name=product.name,
            quantity=product.quantity,
            price=product.price,
        )
        self.session.add(product_orm)

    def get(self, product_id: int) -> Product:
        product_orm = self.session.query(ProductORM).filter_by(id=product_id).one()
        return Product(
            id=product_orm.id,
            name=product_orm.name,
            quantity=product_orm.quantity,
            price=product_orm.price,
        )

    def get_by_name(self, name: str) -> Product:
        orm = self.session.query(ProductORM).filter_by(name=name).one_or_none()
        if orm is None:
            raise ValueError(f"Product with name {name} not found")
        return orm.to_model()

    def list(self) -> List[Product]:
        products_orm = self.session.query(ProductORM).all()
        return [
            Product(id=p.id, name=p.name, quantity=p.quantity, price=p.price)
            for p in products_orm
        ]

    def update(self, product: Product):
        self.session.merge(ProductORM.from_model(product))


class SqlAlchemyOrderRepository(OrderRepository):
    def __init__(self, session: Session):
        self.session = session

    def add(self, order: Order):
        order_orm = OrderORM()
        order_orm.products = [
            self.session.query(ProductORM).filter_by(id=p.id).one()
            for p in order.products
        ]
        self.session.add(order_orm)

    def get(self, order_id: int) -> Order:
        order_orm = self.session.query(OrderORM).filter_by(id=order_id).one()
        products = [
            Product(id=p.id, name=p.name, quantity=p.quantity, price=p.price)
            for p in order_orm.products
        ]
        return Order(id=order_orm.id, products=products)

    def list(self) -> List[Order]:
        orders_orm = self.session.query(OrderORM).all()
        orders = []
        for order_orm in orders_orm:
            products = [
                Product(id=p.id, name=p.name, quantity=p.quantity, price=p.price)
                for p in order_orm.products
            ]
            orders.append(Order(id=order_orm.id, products=products))
        return orders
