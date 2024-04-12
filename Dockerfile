FROM python:3.11

ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN pip install --upgrade pip "poetry==1.8.2"
RUN poetry config virtualenvs.create false --local
COPY pyproject.toml poetry.lock ./
COPY frontend /app/frontend
RUN poetry install

COPY .env ./
COPY backend /app/backend
WORKDIR /app/backend/webshop
RUN rm -rf /app/backend/webshop/uploads/

COPY entrypoint.sh /app/
RUN chmod +x /app/entrypoint.sh
ENTRYPOINT ["/app/entrypoint.sh"]

CMD ["gunicorn", "webshop.wsgi:application", "--bind", "0.0.0.0:8000"]
