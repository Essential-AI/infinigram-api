-- Initialize the database for infini-gram
CREATE USER "infini-gram" WITH PASSWORD 'llmz';
CREATE DATABASE "infini-gram" OWNER "infini-gram";
GRANT ALL PRIVILEGES ON DATABASE "infini-gram" TO "infini-gram";
GRANT ALL ON SCHEMA public TO "infini-gram"; 