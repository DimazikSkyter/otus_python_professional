from typing import List, Tuple

from .exceptions import InsufficientStockError
from .models import Order, Product
from .unit_of_work import UnitOfWork


class WarehouseService:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    def find_product_by_name(self, name: str):
        with self.uow:
            return self.uow.products.get_by_name(name)

    def create_product(self, name: str, quantity: int, price: float) -> Product:
        with self.uow:
            product = Product(id=None, name=name, quantity=quantity, price=price)
            self.uow.products.add(product)
            self.uow.commit()
            return product

    def create_order(self, items: List[Tuple[str, int]]) -> Order:
        with self.uow:
            ordered_products = []

            for name, quantity in items:
                product = self.uow.products.get_by_name(name)
                if product.quantity < quantity:
                    raise InsufficientStockError(
                        product.name, quantity, product.quantity
                    )
                product.quantity -= quantity
                self.uow.products.update(product)
                ordered_products.append(product)
            order = Order(id=None, products=ordered_products)
            self.uow.orders.add(order)
            self.uow.commit()
            return order
