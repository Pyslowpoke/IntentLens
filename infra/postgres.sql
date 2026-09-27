CREATE TABLE orders (id INTEGER PRIMARY KEY, region TEXT, amount DOUBLE PRECISION);
INSERT INTO orders VALUES (1,'East',100),(2,'West',200),(3,'East',300);
CREATE ROLE workbench_reader LOGIN PASSWORD 'fixture_reader_only';
GRANT CONNECT ON DATABASE workbench_test TO workbench_reader;
GRANT USAGE ON SCHEMA public TO workbench_reader;
GRANT SELECT ON orders TO workbench_reader;
ALTER ROLE workbench_reader SET default_transaction_read_only = on;
