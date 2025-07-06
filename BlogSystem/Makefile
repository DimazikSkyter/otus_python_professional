cd E:\Github\otus_python_professional\BlogSystem

# (установим PYTHONPATH для импорта poll_app.*)
$env:PYTHONPATH = "."

# создаём миграции
poetry run python poll_app/manage.py makemigrations

# применяем миграции
poetry run python poll_app/manage.py migrate

# запускаем сервер
poetry run python poll_app/manage.py runserver 0.0.0.0:8000
