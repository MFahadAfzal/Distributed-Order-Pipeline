CREATE TABLE IF NOT EXISTS product (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100),
    amount INT,
    reserved INT
);

CREATE TABLE IF NOT EXISTS reservation (
    id SERIAL PRIMARY KEY,
    order_id INT,
    product_id INT REFERENCES product(id),
    amount INT,
    status VARCHAR(50)
);