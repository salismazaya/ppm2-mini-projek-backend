FROM ghcr.io/astral-sh/uv:python3.11-alpine

WORKDIR /app

COPY pyproject.toml .
COPY .python-version .
COPY uv.lock .

RUN uv sync
RUN uv pip install waitress psycopg2-binary

COPY . .

RUN uv run manage.py collectstatic --no-input

CMD ["uv", "run", "waitres", "--listen=0.0.0.0:8000", "--app=project.wsgi:application"]