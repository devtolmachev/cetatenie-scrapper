#!/bin/bash

set -e 

echo $USER
psql --username postgres --dbname $POSTGRES_DB -f /docker-entrypoint-initdb.d/${POSTGRES_DB}.dump
