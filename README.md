# Webshop

## Quick start
Here is the minimal configuration to start with.

Create a `.env` file from a template:
* `cp .env.template .env`

Change the following variables there:
* `DJANGO_DB_PASSWORD` - create a strong root password.
* `DJANGO_SECRET_KEY` - be sure to generate a random unique key! For this, you can run `openssl rand -hex 32`
* `DJANGO_ALLOWED_HOSTS` - IP addresses and/or domain names which the web shop must be accessible from.

After configuring, run the webshop in a Docker container:
* `docker compose build`
* `docker compose up`

If needed, you can change other variables in the `.env` file - see [Other .env variables](#-other-.env-variables).

## Sample data
In debug mode, sample data is loaded automatically from `db.sqlite3` file - see `DJANGO_DEBUG` in [Other .env variables](#-other-.env-variables).

To load sample data into a Docker container:
* Ensure you've done steps from the [Quick start](#-quick-start) section. When the `webshop_app` container has finished with database migrations and collecting static files, you can add sample data to your webshop by running `docker_add_sample_data.sh`

## Other .env variables
* `DJANGO_DEBUG` - debug mode (`true` or `false`).
* `DJANGO_LOGLEVEL` - logging level. Possible values: debug, info, warning, error, and critical.
* `DJANGO_DB_HOST` - the web shop database host defined in `docker-compose.yaml`. Usually, there is no need to change this variable. But if changed, it must be changed both in `.env` and `docker-compose.yaml`
* `DJANGO_DB_PORT` - database port number.
* `DJANGO_DB_NAME` - database name.

## Running locally and debugging
* You may need to install poetry: `pip install poetry`
* Install dependencies: `poetry install`
* Set `DJANGO_DEBUG` to `true` in the `.env` file
* Run `python manage.py runserver`

For debugging, the SQLite database is used.

## Running unit tests
* `cd backend/webshop/`
* `pytest`

## User credentials
User `admin` exists both locally and in a Docker container. The password is also `admin`. Be sure to change this password in production!

In case you use sample data in a Docker container, these users exist there:
| user | password |
| --- | --- |
| admin | admin |
| 12 | 123qazxsw |
