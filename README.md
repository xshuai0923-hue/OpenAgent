# AOS

Personal Agent Operating System API, built with FastAPI.

## Requirements

- Python 3.11
- Docker with Docker Compose (optional)

## Local development

Create and activate a virtual environment, then install the project and development
tools:

```bash
python -m venv .venv
python -m pip install --upgrade pip
python -m pip install --requirement requirements-dev.lock
```

Start the API locally:

```bash
uvicorn app.main:app --reload
```

The API is available at `http://localhost:8000`. Its health endpoint is
`http://localhost:8000/health`.

## Quality checks

Run the tests and code-quality checks:

```bash
pytest
ruff check .
black --check .
```

Install and run all pre-commit hooks:

```bash
pre-commit install
pre-commit run --all-files
```

After changing dependencies in `pyproject.toml`, regenerate the Linux runtime lock
inside the same Python base image used by Docker, then regenerate the local
development lock:

```bash
docker run --rm --volume "$PWD:/src" --workdir /src python:3.11-slim \
  sh -c "pip install pip-tools && pip-compile --strip-extras \
  --output-file requirements.lock pyproject.toml"
pip-compile --strip-extras --extra dev --output-file requirements-dev.lock pyproject.toml
```

## Docker

Build and start the API:

```bash
docker compose up --build -d
```

Check the service status, then stop it:

```bash
docker compose ps
docker compose down
```
