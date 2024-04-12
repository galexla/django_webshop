#!/bin/bash

cd backend/webshop/

echo "Loading data into DB..."
docker exec -it webshop_app python manage.py loaddata --ignorenonexistent "./fixtures/sample_data.json"

echo "Copying media directory..."
docker cp ./uploads webshop_app:/app/backend/webshop/
