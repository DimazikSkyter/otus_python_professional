.PHONY: lint test check run

# Линтинг кода
lint:
	poetry run pre-commit run --all-files

# Запуск тестов
test:
	poetry run pytest -v --maxfail=1

# Полная проверка: линт + тесты
check:
	make lint
	make test

# Запуск приложения
run:
	poetry run python src/ru/otus/loganalyser/log_analyser.py --config src/ru/otus/loganalyser/config.json
