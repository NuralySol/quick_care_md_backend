CREATE DATABASE quick_care_db;

CREATE USER hospital WITH PASSWORD 'password';

GRANT ALL PRIVILEGES ON DATABASE quick_care_db TO hospital_admin;