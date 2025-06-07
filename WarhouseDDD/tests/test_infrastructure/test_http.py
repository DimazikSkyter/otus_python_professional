from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from infrastructure.api.http import app, get_service
from infrastructure.api.schemas import OrderOut, ProductOut

client = TestClient(app)


def test_create_product_api_mock():
    service_mock = MagicMock()
    service_mock.create_product.return_value = ProductOut(
        id=1, name="Молоко", quantity=5, price=55.0
    )

    app.dependency_overrides[get_service] = lambda: service_mock

    response = client.post(
        "/products", json=[{"name": "Молоко", "quantity": 5, "price": 55.0}]
    )

    assert response.status_code == 200
    data = response.json()
    assert data[0]["name"] == "Молоко"
    assert data[0]["id"] == 1

    service_mock.create_product.assert_called_once()


def test_create_order_api_mock():
    service_mock = MagicMock()
    service_mock.create_order.return_value = OrderOut(
        id=99,
        products=[
            ProductOut(id=1, name="Молоко", quantity=3, price=55.0),
            ProductOut(id=2, name="Хлеб", quantity=2, price=30.0),
        ],
    )

    app.dependency_overrides[get_service] = lambda: service_mock

    response = client.post(
        "/order",
        json=[{"product_id": 1, "quantity": 3}, {"product_id": 2, "quantity": 2}],
    )

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 99
    assert len(data["products"]) == 2
    service_mock.create_order.assert_called_once()
