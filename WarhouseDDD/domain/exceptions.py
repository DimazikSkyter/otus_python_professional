class InsufficientStockError(Exception):
    def __init__(
        self, product_name: str, requested_quantity: int, available_quantity: int
    ):
        self.product_name = product_name
        self.requested_quantity = requested_quantity
        self.available_quantity = available_quantity
        super().__init__(
            f"Product {product_name} doesn't exists in warhouse in {requested_quantity} items, available {available_quantity}"
        )
