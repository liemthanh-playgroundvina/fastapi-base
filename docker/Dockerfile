FROM python:3.9 as builder

WORKDIR /app

COPY requirements.txt .

RUN pip install --user --no-cache-dir -r requirements.txt

FROM python:3.9

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH=/root/.local/bin:$PATH

WORKDIR /app

COPY ./alembic /app/alembic
COPY ./app /app/app
COPY ./static /app/static
COPY ./scripts /app/scripts
COPY ./tests /app/tests
COPY ./logs /app/logs
RUN touch logs/app.log logs/celery.log

COPY --from=builder /root/.local /root/.local

EXPOSE 8000

CMD ["/bin/bash"]
