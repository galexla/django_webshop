# Webshop

## Quick start
Here is the minimal needed configuration:
* Copy the `.env.template` file contents into `.env`: `cp .env.template .env`. Modify the following variables in the `.env`:
* `DJANGO_DB_PASSWORD` - database root password.
* `DJANGO_SECRET_KEY` - be sure to generate a random unique key! For this you can run `openssl rand -hex 32`.
* `DJANGO_ALLOWED_HOSTS` - IP addresses and/or domain names which the web shop must be accessible from.

When the configuration is ready, run the webshop in a docker container:
* Run `docker compose build`
* Then run `docker compose up`

You can edit other variables in the `.env` file - see [Other .env variables](#-other-.env-variables).

## Sample data
In debug mode, sample data is loaded automatically - see `DJANGO_DEBUG` in [Other .env variables](#-other-.env-variables).

To load sample data into the docker container:
* Ensure you've done steps from the [Quick start](#-quick-start) section. When the `webshop_app` container has finished with database migrations and collecting static files, you can add sample data to your webshop by running `docker_add_fixtures.sh`

## Other .env variables
* `DJANGO_DEBUG` - debug mode (`true` or `false`).
* `DJANGO_LOGLEVEL` - logging level. Possible values: debug, info, warning, error, and critical.
* `DJANGO_DB_HOST` - the web shop database host defined in `docker-compose.yaml`. Usually there is not need to change this variable. But if changed, it must be changed in both `.env` and `docker-compose.yaml`.
* `DJANGO_DB_PORT` - database port number.
* `DJANGO_DB_NAME` - database name.

## Debugging
* You may need to install poetry: `pip install poetry`.
* Install dependencies: `poetry install`.
* Set `DJANGO_DEBUG` to `true` and run `python manage.py runserver` locally. For debugging, the SQLite database is used.

## Running unit tests
`python manage.py test`

## User credentials
After `docker compose build` the `admin` user is automatically created. The password is also `admin`. Be sure to change this password in production!

In case you use sample data, these users exist there:
| user | password |
| --- | --- |
| admin | admin |
| 12 | 123qazxsw |
