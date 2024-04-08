#!/bin/bash

cd diploma-backend/webshop/

echo "Loading data into DB..."
docker exec -it webshop_app python manage.py loaddata --ignorenonexistent "./example_fixtures.json"

echo "Copying media directory..."
docker cp ./uploads webshop_app:/app/diploma-backend/webshop/
