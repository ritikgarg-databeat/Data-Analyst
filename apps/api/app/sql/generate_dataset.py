"""Generates the deterministic e-commerce practice dataset used by the SQL Lab.

Usage:
    uv run --project apps/api python -m app.sql.generate_dataset

Writes CSV files to data/sample/ecommerce/. Deterministic (fixed random seed)
so every fresh checkout produces byte-identical data — the SQL exercise
hidden tests in content/exercises/sql/*.yaml depend on this exact dataset.

Grain of each table (see also database/seeds/sql_tables.yaml):
    categories            1 row = 1 product category
    products              1 row = 1 product
    customers             1 row = 1 customer
    marketing_campaigns   1 row = 1 marketing campaign
    sessions              1 row = 1 website/app session
    orders                1 row = 1 order
    order_items           1 row = 1 product line within an order
    payments              1 row = 1 payment transaction for an order

Business consistency is deliberate, not incidental: order_items always sum to
the matching payment amount, payments only exist for orders that were
actually charged (not cancelled/pending), and session timestamps/order dates
never precede a customer's signup_date. Exercises rely on this to have a
single unambiguous correct answer.
"""

from __future__ import annotations

import csv
import random
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path

SEED = 20260301
REPO_ROOT = Path(__file__).resolve().parents[4]
OUTPUT_DIR = REPO_ROOT / "data" / "sample" / "ecommerce"

DATASET_START = date(2024, 1, 1)
DATASET_END = date(2026, 1, 1)
DATASET_DAYS = (DATASET_END - DATASET_START).days

N_CATEGORIES = 10
N_PRODUCTS = 150
N_CUSTOMERS = 1500
N_CAMPAIGNS = 15
N_SESSIONS = 12000

CATEGORY_NAMES = [
    "Electronics",
    "Home & Kitchen",
    "Sports & Outdoors",
    "Books",
    "Toys & Games",
    "Beauty",
    "Apparel",
    "Office Supplies",
    "Pet Supplies",
    "Garden & Outdoor",
]
PRODUCT_ADJECTIVES = ["Premium", "Compact", "Wireless", "Classic", "Pro", "Essential", "Deluxe", "Portable"]
PRODUCT_NOUNS = [
    "Blender",
    "Backpack",
    "Headphones",
    "Notebook",
    "Desk Lamp",
    "Water Bottle",
    "Yoga Mat",
    "Coffee Maker",
    "Board Game",
    "Running Shoes",
    "Bluetooth Speaker",
    "Phone Case",
    "Skincare Set",
    "Office Chair",
    "Garden Hose",
    "Cat Tree",
]
FIRST_NAMES = [
    "Olivia",
    "Liam",
    "Emma",
    "Noah",
    "Ava",
    "Ethan",
    "Sophia",
    "Mason",
    "Isabella",
    "Lucas",
    "Mia",
    "Aiden",
    "Amelia",
    "Jackson",
    "Harper",
    "Logan",
    "Evelyn",
    "Sebastian",
    "Abigail",
    "Owen",
]
LAST_NAMES = [
    "Smith",
    "Johnson",
    "Williams",
    "Brown",
    "Jones",
    "Garcia",
    "Miller",
    "Davis",
    "Rodriguez",
    "Martinez",
    "Hernandez",
    "Lopez",
    "Wilson",
    "Anderson",
    "Thomas",
    "Taylor",
    "Moore",
    "Jackson",
]
COUNTRIES = [
    "United States",
    "Canada",
    "United Kingdom",
    "Germany",
    "France",
    "Australia",
    "Mexico",
    "Brazil",
]
CAMPAIGN_CHANNELS = ["email", "social", "search", "display"]
DEVICES = ["desktop", "mobile", "tablet"]
LANDING_PAGES = ["/home", "/deals", "/category/electronics", "/product-search", "/blog", "/category/apparel"]


@dataclass
class Category:
    category_id: int
    category_name: str
    parent_category: str | None


@dataclass
class Product:
    product_id: int
    product_name: str
    category_id: int
    unit_price: float
    cost: float
    is_active: bool


@dataclass
class Customer:
    customer_id: int
    first_name: str
    last_name: str
    email: str
    country: str
    signup_date: date
    customer_segment: str


@dataclass
class Campaign:
    campaign_id: int
    campaign_name: str
    channel: str
    start_date: date
    end_date: date
    budget: float


def _random_date(rng: random.Random, start: date, end: date) -> date:
    span = (end - start).days
    return start + timedelta(days=rng.randint(0, max(span, 0)))


def _random_datetime(rng: random.Random, start: date, end: date) -> datetime:
    d = _random_date(rng, start, end)
    return datetime(d.year, d.month, d.day, rng.randint(0, 23), rng.randint(0, 59), rng.randint(0, 59))


def generate_categories(rng: random.Random) -> list[Category]:
    return [Category(i + 1, name, None) for i, name in enumerate(CATEGORY_NAMES[:N_CATEGORIES])]


def generate_products(rng: random.Random, categories: list[Category]) -> list[Product]:
    products = []
    for i in range(N_PRODUCTS):
        name = f"{rng.choice(PRODUCT_ADJECTIVES)} {rng.choice(PRODUCT_NOUNS)}"
        category = rng.choice(categories)
        price = round(rng.uniform(5, 500), 2)
        cost = round(price * rng.uniform(0.35, 0.7), 2)
        products.append(Product(i + 1, name, category.category_id, price, cost, rng.random() > 0.05))
    return products


def generate_customers(rng: random.Random) -> list[Customer]:
    customers = []
    for i in range(N_CUSTOMERS):
        first = rng.choice(FIRST_NAMES)
        last = rng.choice(LAST_NAMES)
        signup = _random_date(rng, DATASET_START, DATASET_END - timedelta(days=1))
        segment = "business" if rng.random() < 0.3 else "consumer"
        email = f"{first.lower()}.{last.lower()}{i}@example.com"
        customers.append(Customer(i + 1, first, last, email, rng.choice(COUNTRIES), signup, segment))
    return customers


def generate_campaigns(rng: random.Random) -> list[Campaign]:
    campaigns = []
    for i in range(N_CAMPAIGNS):
        start = _random_date(rng, DATASET_START, DATASET_END - timedelta(days=30))
        end = start + timedelta(days=rng.randint(7, 45))
        channel = rng.choice(CAMPAIGN_CHANNELS)
        campaigns.append(
            Campaign(
                i + 1,
                f"{channel.title()} Campaign {i + 1}",
                channel,
                start,
                end,
                round(rng.uniform(500, 20000), 2),
            )
        )
    return campaigns


def generate_sessions(rng: random.Random, customers: list[Customer], campaigns: list[Campaign]) -> list[dict]:
    sessions = []
    for i in range(N_SESSIONS):
        has_customer = rng.random() < 0.65
        customer = rng.choice(customers) if has_customer else None
        earliest = customer.signup_date if customer else DATASET_START
        start_dt = _random_datetime(rng, earliest, DATASET_END - timedelta(days=1))
        duration_minutes = rng.randint(1, 45)
        end_dt = start_dt + timedelta(minutes=duration_minutes)
        campaign = rng.choice(campaigns) if rng.random() < 0.4 else None
        converted = rng.random() < (0.22 if customer else 0.03)
        sessions.append(
            {
                "session_id": i + 1,
                "customer_id": customer.customer_id if customer else None,
                "session_start": start_dt,
                "session_end": end_dt,
                "device": rng.choice(DEVICES),
                "landing_page": rng.choice(LANDING_PAGES),
                "marketing_campaign_id": campaign.campaign_id if campaign else None,
                "converted": converted,
            }
        )
    return sessions


ORDER_STATUS_WEIGHTS = [("completed", 0.82), ("refunded", 0.06), ("cancelled", 0.09), ("pending", 0.03)]


def _weighted_choice(rng: random.Random, weights: list[tuple[str, float]]) -> str:
    total = sum(w for _, w in weights)
    r = rng.uniform(0, total)
    upto = 0.0
    for value, weight in weights:
        upto += weight
        if upto >= r:
            return value
    return weights[-1][0]


def generate_orders_and_items(
    rng: random.Random, customers: list[Customer], products: list[Product]
) -> tuple[list[dict], list[dict], list[dict]]:
    orders: list[dict] = []
    order_items: list[dict] = []
    payments: list[dict] = []
    order_id = 1
    order_item_id = 1
    payment_id = 1
    active_products = [p for p in products if p.is_active]

    for customer in customers:
        # A light power-law-ish spread: most customers order a handful of times, a few order a lot.
        n_orders = rng.choices([0, 1, 2, 3, 5, 8, 15], weights=[10, 30, 25, 15, 10, 7, 3])[0]
        for _ in range(n_orders):
            order_date = _random_date(rng, customer.signup_date, DATASET_END - timedelta(days=1))
            status = _weighted_choice(rng, ORDER_STATUS_WEIGHTS)
            channel = rng.choices(["web", "mobile", "marketplace"], weights=[55, 35, 10])[0]

            n_items = rng.randint(1, 5)
            chosen_products = rng.sample(active_products, k=min(n_items, len(active_products)))
            order_total = 0.0
            for product in chosen_products:
                quantity = rng.randint(1, 4)
                unit_price = product.unit_price
                discount = round(unit_price * rng.choice([0, 0, 0, 0.1, 0.15, 0.2]), 2)
                line_total = round((unit_price - discount) * quantity, 2)
                order_total += line_total
                order_items.append(
                    {
                        "order_item_id": order_item_id,
                        "order_id": order_id,
                        "product_id": product.product_id,
                        "quantity": quantity,
                        "unit_price": unit_price,
                        "discount": discount,
                    }
                )
                order_item_id += 1
            order_total = round(order_total, 2)

            orders.append(
                {
                    "order_id": order_id,
                    "customer_id": customer.customer_id,
                    "order_date": order_date,
                    "status": status,
                    "channel": channel,
                }
            )

            # Only orders that were actually charged produce a payment row.
            if status in ("completed", "refunded"):
                payment_status = "success" if status == "completed" else "refunded"
                payment_date = order_date + timedelta(days=rng.randint(0, 2))
                payments.append(
                    {
                        "payment_id": payment_id,
                        "order_id": order_id,
                        "payment_date": payment_date,
                        "amount": order_total,
                        "payment_method": rng.choices(
                            ["credit_card", "paypal", "gift_card"], weights=[70, 25, 5]
                        )[0],
                        "status": payment_status,
                    }
                )
                payment_id += 1

            order_id += 1

    return orders, order_items, payments


def _write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def generate() -> dict[str, int]:
    rng = random.Random(SEED)

    categories = generate_categories(rng)
    products = generate_products(rng, categories)
    customers = generate_customers(rng)
    campaigns = generate_campaigns(rng)
    sessions = generate_sessions(rng, customers, campaigns)
    orders, order_items, payments = generate_orders_and_items(rng, customers, products)

    _write_csv(
        OUTPUT_DIR / "categories.csv",
        [
            {
                "category_id": c.category_id,
                "category_name": c.category_name,
                "parent_category": c.parent_category,
            }
            for c in categories
        ],
        ["category_id", "category_name", "parent_category"],
    )
    _write_csv(
        OUTPUT_DIR / "products.csv",
        [
            {
                "product_id": p.product_id,
                "product_name": p.product_name,
                "category_id": p.category_id,
                "unit_price": p.unit_price,
                "cost": p.cost,
                "is_active": p.is_active,
            }
            for p in products
        ],
        ["product_id", "product_name", "category_id", "unit_price", "cost", "is_active"],
    )
    _write_csv(
        OUTPUT_DIR / "customers.csv",
        [
            {
                "customer_id": c.customer_id,
                "first_name": c.first_name,
                "last_name": c.last_name,
                "email": c.email,
                "country": c.country,
                "signup_date": c.signup_date.isoformat(),
                "customer_segment": c.customer_segment,
            }
            for c in customers
        ],
        ["customer_id", "first_name", "last_name", "email", "country", "signup_date", "customer_segment"],
    )
    _write_csv(
        OUTPUT_DIR / "marketing_campaigns.csv",
        [
            {
                "campaign_id": c.campaign_id,
                "campaign_name": c.campaign_name,
                "channel": c.channel,
                "start_date": c.start_date.isoformat(),
                "end_date": c.end_date.isoformat(),
                "budget": c.budget,
            }
            for c in campaigns
        ],
        ["campaign_id", "campaign_name", "channel", "start_date", "end_date", "budget"],
    )
    _write_csv(
        OUTPUT_DIR / "sessions.csv",
        [
            {
                "session_id": s["session_id"],
                "customer_id": s["customer_id"],
                "session_start": s["session_start"].isoformat(sep=" "),
                "session_end": s["session_end"].isoformat(sep=" "),
                "device": s["device"],
                "landing_page": s["landing_page"],
                "marketing_campaign_id": s["marketing_campaign_id"],
                "converted": s["converted"],
            }
            for s in sessions
        ],
        [
            "session_id",
            "customer_id",
            "session_start",
            "session_end",
            "device",
            "landing_page",
            "marketing_campaign_id",
            "converted",
        ],
    )
    _write_csv(
        OUTPUT_DIR / "orders.csv",
        [
            {
                "order_id": o["order_id"],
                "customer_id": o["customer_id"],
                "order_date": o["order_date"].isoformat(),
                "status": o["status"],
                "channel": o["channel"],
            }
            for o in orders
        ],
        ["order_id", "customer_id", "order_date", "status", "channel"],
    )
    _write_csv(
        OUTPUT_DIR / "order_items.csv",
        order_items,
        ["order_item_id", "order_id", "product_id", "quantity", "unit_price", "discount"],
    )
    _write_csv(
        OUTPUT_DIR / "payments.csv",
        [
            {
                "payment_id": p["payment_id"],
                "order_id": p["order_id"],
                "payment_date": p["payment_date"].isoformat(),
                "amount": p["amount"],
                "payment_method": p["payment_method"],
                "status": p["status"],
            }
            for p in payments
        ],
        ["payment_id", "order_id", "payment_date", "amount", "payment_method", "status"],
    )

    return {
        "categories": len(categories),
        "products": len(products),
        "customers": len(customers),
        "marketing_campaigns": len(campaigns),
        "sessions": len(sessions),
        "orders": len(orders),
        "order_items": len(order_items),
        "payments": len(payments),
    }


if __name__ == "__main__":
    counts = generate()
    for table, count in counts.items():
        print(f"{table}: {count} rows")
    print(f"\nWritten to {OUTPUT_DIR}")
