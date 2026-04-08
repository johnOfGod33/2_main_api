#stage 1
FROM python:3.13-slim AS builder

WORKDIR /build

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY app/requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

#stage 2
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/code \
    PATH="/opt/venv/bin:$PATH"

RUN groupadd --system --gid 1000 app \
    && useradd --system --uid 1000 --gid app --no-create-home --shell /usr/sbin/nologin app

WORKDIR /code

COPY --from=builder /opt/venv /opt/venv
COPY --chown=app:app ./app ./app

RUN mkdir -p /code/uploads && chown app:app /code/uploads

USER app

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
