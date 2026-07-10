# aegis_backend/production_settings.py
# Add this to your settings.py or create a separate production file

# IMPORTANT: Add these settings for production
DEBUG = False
ALLOWED_HOSTS = ['*']  # For testing, restrict later

# Database configuration for PostgreSQL (if using)
# Render provides PostgreSQL for free
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.postgresql',
#         'NAME': 'your_db_name',
#         'USER': 'your_user',
#         'PASSWORD': 'your_password',
#         'HOST': 'your_host',
#         'PORT': '5432',
#     }
# }

# Static files
STATIC_ROOT = '/var/www/static/'
