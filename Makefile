.PHONY: install dev api web seed test clean

PYTHON ?= python3

install:
	cd api && $(PYTHON) -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt
	cd web && pnpm install

api:
	cd api && . .venv/bin/activate && uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

web:
	cd web && pnpm dev

dev:
	@echo "Starting API on :8000 and web on :3000"
	@trap 'kill 0' INT; \
		($(MAKE) api &) && \
		($(MAKE) web)

seed:
	cd api && . .venv/bin/activate && python -m app.scripts.seed_personas

test:
	cd api && . .venv/bin/activate && pytest -q
	cd web && pnpm test

clean:
	rm -rf api/.venv api/.pytest_cache web/node_modules web/.next
