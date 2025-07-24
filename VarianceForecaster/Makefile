.PHONY: run-server lint

run-server:
	poetry run uvicorn vf_app.api.endpoints:app --reload --host 0.0.0.0 --port 8000

lint:
	poetry run mypy .
