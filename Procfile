release: python manage.py migrate && python manage.py seed_demo_data
web: gunicorn aegis_backend.wsgi --bind 0.0.0.0:$PORT
