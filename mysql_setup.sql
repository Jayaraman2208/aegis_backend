-- Run this once, logged in as root (mysql -u root -p), before python manage.py migrate.
-- Django will create every table below via migrations — this script only
-- creates the database and a dedicated least-privilege user.

CREATE DATABASE IF NOT EXISTS aegis_db
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

CREATE USER IF NOT EXISTS 'aegis_user'@'%' IDENTIFIED BY 'changeme';

GRANT ALL PRIVILEGES ON aegis_db.* TO 'aegis_user'@'%';
FLUSH PRIVILEGES;

-- After this, run:
--   python manage.py migrate
--   python manage.py createsuperuser
--   python manage.py seed_demo_data
