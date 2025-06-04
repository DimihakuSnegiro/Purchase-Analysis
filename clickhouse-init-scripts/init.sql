CREATE TABLE IF NOT EXISTS customers
(
    customer_id UInt64,
    username String,
    created_at DateTime,
    updated_at DateTime,
    batch_time DateTime
)
ENGINE = MergeTree
ORDER BY (batch_time, customer_id);

CREATE TABLE IF NOT EXISTS sellers
(
    seller_id UInt64,
    username String,
    created_at DateTime,
    updated_at DateTime,
    batch_time DateTime
)
ENGINE = MergeTree
ORDER BY (batch_time, seller_id);

CREATE TABLE IF NOT EXISTS products
(
    product_id UInt64,
    product_name String,
    product_description String,
    category String,
    price Float32,
    seller_id UInt64,
    created_at DateTime,
    updated_at DateTime,
    batch_time DateTime
)
ENGINE = MergeTree
ORDER BY (batch_time, product_id);

CREATE TABLE IF NOT EXISTS fact_sales
(
    sale_id UInt64,
    customer_id UInt64,
    product_id UInt64,
    seller_id UInt64,
    sale_date DateTime,
    quantity UInt32,
    total_amount Float32,
    batch_time DateTime
)
ENGINE = MergeTree
ORDER BY (batch_time, sale_id);

CREATE MATERIALIZED VIEW IF NOT EXISTS daily_sales_by_product
ENGINE = SummingMergeTree()
ORDER BY (sale_date, product_id)
POPULATE
AS
SELECT
    toDate(fs.sale_date) AS sale_date,
    fs.product_id,
    sum(fs.quantity) AS total_quantity,
    sum(fs.total_amount) AS total_amount
FROM fact_sales fs
INNER JOIN products p ON fs.product_id = p.product_id
INNER JOIN sellers s ON fs.seller_id = s.seller_id
INNER JOIN customers c ON fs.customer_id = c.customer_id
GROUP BY sale_date, fs.product_id;

CREATE MATERIALIZED VIEW IF NOT EXISTS daily_sales_by_seller
ENGINE = SummingMergeTree()
ORDER BY (sale_date, seller_id)
POPULATE
AS
SELECT
    toDate(fs.sale_date) AS sale_date,
    fs.seller_id,
    sum(fs.quantity) AS total_quantity,
    sum(fs.total_amount) AS total_amount
FROM fact_sales fs
INNER JOIN products p ON fs.product_id = p.product_id
INNER JOIN sellers s ON fs.seller_id = s.seller_id
INNER JOIN customers c ON fs.customer_id = c.customer_id
GROUP BY sale_date, fs.seller_id;

CREATE MATERIALIZED VIEW IF NOT EXISTS daily_sales_by_customer
ENGINE = SummingMergeTree()
ORDER BY (sale_date, customer_id)
POPULATE
AS
SELECT
    toDate(fs.sale_date) AS sale_date,
    fs.customer_id,
    sum(fs.quantity) AS total_quantity,
    sum(fs.total_amount) AS total_amount
FROM fact_sales fs
INNER JOIN products p ON fs.product_id = p.product_id
INNER JOIN sellers s ON fs.seller_id = s.seller_id
INNER JOIN customers c ON fs.customer_id = c.customer_id
GROUP BY sale_date, fs.customer_id;

CREATE MATERIALIZED VIEW IF NOT EXISTS monthly_sales_by_product
ENGINE = SummingMergeTree()
ORDER BY (sale_month, product_id)
POPULATE
AS
SELECT
    toStartOfMonth(fs.sale_date) AS sale_month,
    fs.product_id,
    sum(fs.quantity) AS total_quantity,
    sum(fs.total_amount) AS total_amount
FROM fact_sales fs
INNER JOIN products p ON fs.product_id = p.product_id
INNER JOIN sellers s ON fs.seller_id = s.seller_id
INNER JOIN customers c ON fs.customer_id = c.customer_id
GROUP BY sale_month, fs.product_id;

CREATE MATERIALIZED VIEW IF NOT EXISTS monthly_sales_by_seller
ENGINE = SummingMergeTree()
ORDER BY (sale_month, seller_id)
POPULATE
AS
SELECT
    toStartOfMonth(fs.sale_date) AS sale_month,
    fs.seller_id,
    sum(fs.quantity) AS total_quantity,
    sum(fs.total_amount) AS total_amount
FROM fact_sales fs
INNER JOIN products p ON fs.product_id = p.product_id
INNER JOIN sellers s ON fs.seller_id = s.seller_id
INNER JOIN customers c ON fs.customer_id = c.customer_id
GROUP BY sale_month, fs.seller_id;

CREATE MATERIALIZED VIEW IF NOT EXISTS monthly_sales_by_customer
ENGINE = SummingMergeTree()
ORDER BY (sale_month, customer_id)
POPULATE
AS
SELECT
    toStartOfMonth(fs.sale_date) AS sale_month,
    fs.customer_id,
    sum(fs.quantity) AS total_quantity,
    sum(fs.total_amount) AS total_amount
FROM fact_sales fs
INNER JOIN products p ON fs.product_id = p.product_id
INNER JOIN sellers s ON fs.seller_id = s.seller_id
INNER JOIN customers c ON fs.customer_id = c.customer_id
GROUP BY sale_month, fs.customer_id;

CREATE MATERIALIZED VIEW IF NOT EXISTS top_products_by_quantity
ENGINE = SummingMergeTree()
ORDER BY (product_id)
POPULATE
AS
SELECT
    product_id,
    sum(quantity) AS total_quantity_sold
FROM fact_sales
GROUP BY product_id;


CREATE MATERIALIZED VIEW IF NOT EXISTS top_customers_by_amount
ENGINE = SummingMergeTree()
ORDER BY (customer_id)
POPULATE
AS
SELECT
    customer_id,
    sum(total_amount) AS total_amount_spent
FROM fact_sales
GROUP BY customer_id;

CREATE MATERIALIZED VIEW IF NOT EXISTS top_sellers_by_revenue
ENGINE = SummingMergeTree()
ORDER BY (seller_id)
POPULATE
AS
SELECT
    seller_id,
    sum(total_amount) AS total_revenue
FROM fact_sales
GROUP BY seller_id;

CREATE MATERIALIZED VIEW IF NOT EXISTS top_sellers_by_quantity
ENGINE = SummingMergeTree()
ORDER BY (seller_id)
POPULATE
AS
SELECT
    seller_id,
    sum(quantity) AS total_quantity_sold
FROM fact_sales
GROUP BY seller_id;

CREATE MATERIALIZED VIEW IF NOT EXISTS average_sale_check
ENGINE = AggregatingMergeTree()
ORDER BY ()
POPULATE
AS
SELECT
    sum(total_amount) AS total_revenue,
    count(sale_id) AS total_sales_count
FROM fact_sales;