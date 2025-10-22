FROM python:3.12-alpine AS prepare
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=1

RUN pip install poetry==2.2.1
COPY pyproject.toml poetry.lock ./


FROM prepare AS dependencies
RUN poetry install --no-root --no-ansi


FROM python:3.12-alpine
ENV PATH="/.venv/bin:$PATH" \
    VIRTUAL_ENV=/.venv \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

COPY --from=dependencies ${VIRTUAL_ENV} ${VIRTUAL_ENV}
WORKDIR /src
COPY ./src .