FROM python:3.11

ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN pip install --upgrade pip "poetry==1.8.2"
RUN poetry config virtualenvs.create false --local
COPY pyproject.toml poetry.lock ./
COPY diploma-frontend /app/diploma-frontend
RUN poetry install

COPY diploma-backend /app/diploma-backend
WORKDIR /app/diploma-backend/webshop
RUN python manage.py collectstatic --noinput
RUN python manage.py migrate

CMD ["gunicorn", "webshop.wsgi:application", "--bind", "0.0.0.0:8000"]
