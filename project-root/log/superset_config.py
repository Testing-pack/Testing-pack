# superset_config.py
import os

SECRET_KEY = os.environ.get('SUPERSET_SECRET_KEY', 'supersecret_key_change_me_in_prod')
SQLALCHEMY_DATABASE_URI = os.environ.get('SUPERSET_DB_URI', 'postgresql+psycopg2://airflow:airflow@postgres/superset')