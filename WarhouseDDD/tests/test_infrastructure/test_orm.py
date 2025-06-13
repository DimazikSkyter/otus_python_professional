from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from infrastructure.orm import Base, ProductORM


def test_product_orm_persistence():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    product = ProductORM(name="Тест", quantity=5, price=99.9)
    session.add(product)
    session.commit()

    retrieved = session.query(ProductORM).first()

    assert retrieved.name == "Тест"
    assert retrieved.quantity == 5
    assert retrieved.price == 99.9
    assert retrieved.id is not None
