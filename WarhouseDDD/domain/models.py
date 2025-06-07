from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Product:
    id: Optional[int]
    name: str
    quantity: int
    price: float


@dataclass
class Order:
    id: Optional[int]
    products: List[Product] = field(default_factory=list)

    def add_product(self, product: Product):
        self.products.append(product)
