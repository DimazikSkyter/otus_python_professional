from typing import List

from sqlalchemy import Column, Float, ForeignKey, Integer, String, Table
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from domain.models import Product


class Base(DeclarativeBase):
    pass


class ProductORM(Base):
    __tablename__ = "products"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String)
    quantity: Mapped[int] = mapped_column(Integer)
    price: Mapped[float] = mapped_column(Float)

    def to_model(self):
        return Product(self.id, self.name, self.quantity, self.price)

    @staticmethod
    def from_model(product: Product) -> "ProductORM":
        return ProductORM(
            id=product.id,
            name=product.name,
            quantity=product.quantity,
            price=product.price,
        )


order_product_assocoations = Table(
    "order_product_assocoations",
    Base.metadata,
    Column("order_id", ForeignKey("orders.id"), primary_key=True),
    Column("product_id", ForeignKey("products.id"), primary_key=True),
)


class OrderORM(Base):
    __tablename__ = "orders"
    id: Mapped[int] = mapped_column(primary_key=True)
    products: Mapped[List[ProductORM]] = relationship(
        secondary=order_product_assocoations
    )
