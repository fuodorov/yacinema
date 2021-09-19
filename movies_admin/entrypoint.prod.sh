#!/bin/sh

if [ "$DB_DATABASE" = "postgres" ]
then
    echo "Waiting for postgres..."

    while ! nc -z $DB_HOST $DB_PORT; do
      sleep 0.1s
    done

    echo "PostgreSQL started"
fi

python utils/schema_design/schema_design.py
python utils/sqlite_to_postgres/load_data.py

python manage.py flush --no-input
python manage.py collectstatic --no-input --clear
python manage.py makemigrations --no-input
python manage.py migrate --noinput

echo "from django.contrib.auth.models import User;
User.objects.filter(email='$DJANGO_ADMIN_EMAIL').delete();
User.objects.create_superuser('$DJANGO_ADMIN_USERNAME', '$DJANGO_ADMIN_EMAIL', '$DJANGO_ADMIN_PASSWORD');
" | python manage.py shell

exec "$@"