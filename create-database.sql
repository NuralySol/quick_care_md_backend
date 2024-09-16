-- Step 1: Create the database
CREATE DATABASE quick_care_db;

-- Step 2: Create a new user (hospital_admin in this case)
CREATE USER hospital_admin WITH PASSWORD 'password';

-- Step 3: Grant all privileges on the new database to the user
GRANT ALL PRIVILEGES ON DATABASE quick_care_db TO hospital_admin;