FROM python:3.10-slim

# рабочая директория в контейнере
WORKDIR /app

# скопировать зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# скопировать всё содержимое проекта
COPY . .

# Hugging Face Spaces слушает на 7860
# app = FastAPI(...) находится в tg_app/main.py → модуль tg_app.main
CMD ["uvicorn", "tg_app.main:app", "--host", "0.0.0.0", "--port", "7860"]