from typing import List, Optional

from pydantic import BaseModel


class ProductIn(BaseModel):
    name: str
    quantity: int
    price: float


class ProductOut(BaseModel):
    id: Optional[int]
    name: str
    quantity: int
    price: float


class OrderItemIn(BaseModel):
    product_name: str
    quantity: int


class OrderOut(BaseModel):
    id: Optional[int]
    products: List[ProductOut]
