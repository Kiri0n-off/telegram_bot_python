CREATE USER replicator REPLICATION LOGIN ENCRYPTED PASSWORD 'Qq123456';
SELECT pg_create_physical_replication_slot('replication_slot');

CREATE TABLE phones (
    id SERIAL PRIMARY KEY,
    phone VARCHAR(50) NOT NULL
);

CREATE TABLE emails (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) NOT NULL
);

INSERT INTO phones (phone) VALUES ('88008080'), ('8(800)3553535');
INSERT INTO emails (email) VALUES ('kirichenko@pt.com'), ('ptstart@pt.local');