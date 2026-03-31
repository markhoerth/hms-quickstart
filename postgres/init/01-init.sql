CREATE DATABASE hms_meta;
CREATE USER gravitino WITH PASSWORD 'gravitino';
GRANT ALL PRIVILEGES ON DATABASE hms_meta TO gravitino;
\c hms_meta
GRANT ALL ON SCHEMA public TO gravitino;
