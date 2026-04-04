.PHONY: bot db

bot:
	cd bot && uv run uvicorn main:app --host 0.0.0.0 --port 8000 --reload

db:
	cd bot && uv run datasette main.db --open
