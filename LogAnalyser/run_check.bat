@echo off
poetry lock
poetry install
poetry run black src tests
poetry run ruff check src tests
poetry run pytest -q
