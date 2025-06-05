import clickhouse_connect
from faker import Faker
import random
from datetime import datetime, timedelta
import pytz 

fake = Faker('en_US')

CLICKHOUSE_HOST = 'localhost'
CLICKHOUSE_PORT = 8123
CLICKHOUSE_USER = 'clickhouse'
CLICKHOUSE_PASSWORD = 'clickpass'

NUM_CUSTOMERS = 100
NUM_SELLERS = 20
NUM_PRODUCTS = 200
NUM_SALES = 10000

TZ = pytz.UTC

def generate_customers(num_customers):
    customers = []
    start_date = datetime.now(TZ) - timedelta(days=60)
    for i in range(num_customers):
        customer_id = i + 1
        username = fake.user_name()
        created_at = TZ.localize(fake.date_time_between(start_date=start_date, end_date='now'))
        updated_at = TZ.localize(fake.date_time_between(start_date=created_at, end_date='now'))
        customers.append((customer_id, username, created_at, updated_at))
    print(f"Generated {len(customers)} customers.")
    return customers

def generate_sellers(num_sellers):
    sellers = []
    start_date = datetime.now(TZ) - timedelta(days=60)
    for i in range(num_sellers):
        seller_id = i + 1
        username = fake.company() + " Seller"
        created_at = TZ.localize(fake.date_time_between(start_date=start_date, end_date='now'))
        updated_at = TZ.localize(fake.date_time_between(start_date=created_at, end_date='now'))
        sellers.append((seller_id, username, created_at, updated_at))
    print(f"Generated {len(sellers)} sellers.")
    return sellers

def generate_products(num_products, seller_ids):
    products = []
    categories = ['Electronics', 'Clothing', 'Books', 'Home', 'Toys']
    start_date = datetime.now(TZ) - timedelta(days=60)
    for i in range(num_products):
        product_id = i + 1
        product_name = fake.catch_phrase() + " " + fake.word()
        product_description = fake.paragraph(nb_sentences=3)
        category = random.choice(categories)
        price = round(random.uniform(5.0, 1000.0), 2)
        seller_id = random.choice(seller_ids)
        created_at = TZ.localize(fake.date_time_between(start_date=start_date, end_date='now'))
        updated_at = TZ.localize(fake.date_time_between(start_date=created_at, end_date='now'))
        products.append((product_id, product_name, product_description, category, price, seller_id, created_at, updated_at))
    print(f"Generated {len(products)} products.")
    return products

def generate_sales(num_sales, customer_ids, product_ids, seller_ids, products_data):
    sales = []
    start_date = datetime.now(TZ) - timedelta(days=60)
    product_prices = {p[0]: p[4] for p in products_data}
    for i in range(num_sales):
        sale_id = i + 1
        customer_id = random.choice(customer_ids)
        product_id = random.choice(product_ids)
        seller_id = random.choice(seller_ids)
        sale_date = TZ.localize(fake.date_time_between(start_date=start_date, end_date='now'))
        quantity = random.randint(1, 5)
        price = product_prices.get(product_id, 50.0)
        total_amount = round(price * quantity, 2)
        sales.append((sale_id, customer_id, product_id, seller_id, sale_date, quantity, total_amount))
    print(f"Generated {len(sales)} sales.")
    return sales

def insert_data(client, table_name, columns, data):
    print(f"Inserting {len(data)} records into {table_name}...")
    if data:
        client.insert(table_name, data, column_names=columns)
        print(f"Successfully inserted into {table_name}.")
    else:
        print(f"No data to insert into {table_name}.")

def main():
    try:
        client = clickhouse_connect.get_client(
            host=CLICKHOUSE_HOST,
            port=CLICKHOUSE_PORT,
            username=CLICKHOUSE_USER,
            password=CLICKHOUSE_PASSWORD
        )
        print("Connected to ClickHouse.")

        customers_data = generate_customers(NUM_CUSTOMERS)
        customer_ids = [c[0] for c in customers_data]
        insert_data(client, 'customers', ['customer_id', 'username', 'created_at', 'updated_at'], customers_data)

        sellers_data = generate_sellers(NUM_SELLERS)
        seller_ids = [s[0] for s in sellers_data]
        insert_data(client, 'sellers', ['seller_id', 'username', 'created_at', 'updated_at'], sellers_data)

        products_data = generate_products(NUM_PRODUCTS, seller_ids)
        product_ids = [p[0] for p in products_data]
        insert_data(client, 'products', ['product_id', 'product_name', 'product_description', 'category', 'price', 'seller_id', 'created_at', 'updated_at'], products_data)

        sales_data = generate_sales(NUM_SALES, customer_ids, product_ids, seller_ids, products_data)
        insert_data(client, 'fact_sales', ['sale_id', 'customer_id', 'product_id', 'seller_id', 'sale_date', 'quantity', 'total_amount'], sales_data)

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if 'client' in locals() and client:
            client.close()
            print("ClickHouse connection closed.")

if __name__ == '__main__':
    main()
