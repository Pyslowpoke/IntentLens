USE workbench_test;
CREATE TABLE orders (id INTEGER PRIMARY KEY, region VARCHAR(40), amount DOUBLE);
INSERT INTO orders VALUES (1,'East',100),(2,'West',200),(3,'East',300);
CREATE USER 'workbench_reader'@'%' IDENTIFIED BY 'fixture_reader_only';
GRANT SELECT ON workbench_test.* TO 'workbench_reader'@'%';
