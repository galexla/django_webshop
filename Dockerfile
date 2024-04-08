FROM python:3.11

ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN pip install --upgrade pip "poetry==1.8.2"
RUN poetry config virtualenvs.create false --local
COPY pyproject.toml poetry.lock ./
COPY diploma-frontend /app/diploma-frontend
RUN poetry install

COPY .env ./
COPY diploma-backend /app/diploma-backend
WORKDIR /app/diploma-backend/webshop
RUN rm -rf /app/diploma-backend/webshop/uploads/

COPY entrypoint.sh /app/
RUN chmod +x /app/entrypoint.sh
ENTRYPOINT ["/app/entrypoint.sh"]

CMD ["gunicorn", "webshop.wsgi:application", "--bind", "0.0.0.0:8000"]
