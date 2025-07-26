from passlib.context import CryptContext
from vf_app.storage.persistence import SessionLocal, UserModel, init_db

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_user(username: str, email: str, age: int, password: str):
    init_db()
    db = SessionLocal()
    if db.query(UserModel).filter(UserModel.username == username).first():
        print("Пользователь уже существует")
        return
    hashed = pwd_context.hash(password)
    user = UserModel(username=username, email=email, age=age, hashed_password=hashed)
    db.add(user)
    db.commit()
    print(f"Пользователь {username} создан")


if __name__ == "__main__":
    # Можешь подставить свои значения
    create_user("admin", "admin@example.com", 30, "admin123")
