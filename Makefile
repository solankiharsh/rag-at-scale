.PHONY: start start_workers
start:
	poetry run uvicorn app:app --reload --host 0.0.0.0 --port 8000
start_workers:
	./alembic/alembic_upgrade.sh && poetry run gunicorn -c gunicorn.conf.py rag_service.main:app
start_celery:
	poetry run celery -A celery_config worker --queues=celery,data_extraction,data_processing,data_embed_ingest --loglevel=info --pool=gevent --concurrency=10 --max-tasks-per-child=1000 --max-memory-per-child=1000000 --max-tasks-per-child=1000 --max-memory-per-child=1000000 --prefetch-multiplier=1
start_celery_beat:
	poetry run celery -A celery_config beat --loglevel=info
start_celery_flower:
	poetry run celery -A celery_config flower --loglevel=info
.PHONY: mypy
mypy:
	poetry run dotenv run mypy .

.PHONY: test
test:
	./alembic/alembic_upgrade.sh && poetry run dotenv run coverage run -m pytest
	poetry run dotenv run coverage report -m

.PHONY: tests_profile
tests_profile:
	poetry run dotenv run pytest --profile

.PHONY: lint
lint:
	poetry run ruff format .
	poetry run ruff check .

.PHONY: locust
locust:
	poetry run locust -f tests/performance/locustfile.py --config tests/performance/locust.conf

.PHONY: checks
checks:
	poetry run ruff format .
	poetry run ruff check .
	poetry run dotenv run mypy .
	poetry run dotenv run pytest
	poetry run dotenv run coverage run -m pytest
	poetry run dotenv run coverage report -m

.PHONY: docs
docs:
	poetry run python api-spec/generate_docs.py

.PHONY: upgrade_db
upgrade_db:
	./alembic/alembic_upgrade.sh

.PHONY: downgrade_db
downgrade_db:
	./alembic/alembic_downgrade.sh

.PHONY: new_db_revision
new_db_revision:
	./alembic/alembic_new_revision.sh $(name)
