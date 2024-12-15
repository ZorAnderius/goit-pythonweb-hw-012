#!/bin/bash

echo "Waiting for postgres to be ready..."
./wait-for-it.sh postgres:5432 --timeout=30 --strict -- echo "PostgreSQL is ready!"

echo "Checking if database exists..."
DB_EXISTS=$(PGPASSWORD=$POSTGRES_PASSWORD psql -h postgres -U $POSTGRES_USER -tc "SELECT 1 FROM pg_database WHERE datname = '${POSTGRES_DB}'" | tr -d '[:space:]')
if [ "$DB_EXISTS" != "1" ]; then
    echo "Database '${POSTGRES_DB}' does not exist. Creating..."
    PGPASSWORD=$POSTGRES_PASSWORD psql -h postgres -U $POSTGRES_USER -c "CREATE DATABASE ${POSTGRES_DB}"
else
    echo "Database '${POSTGRES_DB}' already exists."
fi

echo "Database is ready."

echo "Checking if alembic_version table exists or is empty..."

echo "Applying migrations..."
alembic upgrade head
if [ $? -eq 0 ]; then
    echo "Migrations applied successfully."
else
    echo "Migrations failed."
    exit 1
fi


ALCHEMIC_TABLE_CHECK=$(PGPASSWORD=$POSTGRES_PASSWORD psql -h postgres -U $POSTGRES_USER -d $POSTGRES_DB -tc "SELECT to_regclass('public.alembic_version');" | tr -d '[:space:]')

if [ "$ALCHEMIC_TABLE_CHECK" == "NULL" ]; then
    echo "alembic_version table does not exist. Creating migration files..."
    alembic revision --autogenerate -m 'Init'
    alembic upgrade head
    if [ $? -eq 0 ]; then
        echo "Migration files generated successfully."
    else
        echo "Failed to generate migration files."
        exit 1
    fi
else
    ALCHEMIC_VERSION_COUNT=$(PGPASSWORD=$POSTGRES_PASSWORD psql -h postgres -U $POSTGRES_USER -d $POSTGRES_DB -tc "SELECT COUNT(*) FROM alembic_version;")

    if [ "$ALCHEMIC_VERSION_COUNT" -eq 0 ]; then
        echo "alembic_version table is empty. Generating initial migration files..."
        alembic revision --autogenerate -m 'Init'
        alembic upgrade head
        if [ $? -eq 0 ]; then
            echo "Migration files generated successfully."
        else
            echo "Failed to generate migration files."
            exit 1
        fi
    else
        echo "alembic_version table is already populated."
    fi
fi

echo "Starting the application..."
uvicorn main:app --host 0.0.0.0 --port 8000