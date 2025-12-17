FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV POETRY_VERSION=2.2.0
ENV FASTMCP_EXPERIMENTAL_ENABLE_NEW_OPENAPI_PARSER=true

WORKDIR /app

RUN pip install --upgrade pip \
 && pip install poetry==$POETRY_VERSION --no-cache-dir \
 && poetry config virtualenvs.create false

COPY pyproject.toml poetry.lock ./

RUN poetry install --only=main --no-root

COPY src ./src

RUN groupadd -r mcpuser && useradd -r -g mcpuser mcpuser

RUN chown -R mcpuser:mcpuser /app

USER mcpuser

CMD ["python", "src/main.py"]