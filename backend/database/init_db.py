"""
Database Initialization & Migrations
"""
from .connection import engine, Base, SessionLocal
from .catalog_sync import apply_catalog_config
from .models import (
    User, Product, Invoice, ChatSession, ChatMessage,
    EmployeeMeeting, EmployeeEmail, LeaveRequest, CompanyProject, JiraTicket
)

def init_db():
    Base.metadata.create_all(bind=engine)
    with engine.connect() as conn:
        import sqlite3
        raw_conn = conn.connection
        cursor = raw_conn.cursor()

        # Check and migrate users columns
        cursor.execute("PRAGMA table_info(users)")
        user_cols = [c[1] for c in cursor.fetchall()]
        if "role" not in user_cols:
            cursor.execute("ALTER TABLE users ADD COLUMN role TEXT DEFAULT 'customer'")
        if "name" not in user_cols:
            cursor.execute("ALTER TABLE users ADD COLUMN name TEXT DEFAULT 'Maya Sharma'")

        # Check and migrate products columns
        cursor.execute("PRAGMA table_info(products)")
        prod_cols = [c[1] for c in cursor.fetchall()]
        migrations = [
            ("rating", "REAL DEFAULT 4.5"),
            ("review_count", "INTEGER DEFAULT 120"),
            ("category", "TEXT DEFAULT 'Office Tech'"),
            ("discount_percent", "INTEGER DEFAULT 15"),
            ("image_url", "TEXT"),
            ("delivery_estimate", "TEXT DEFAULT 'Tomorrow, 11 AM'"),
        ]
        for col_name, col_def in migrations:
            if col_name not in prod_cols:
                cursor.execute(f"ALTER TABLE products ADD COLUMN {col_name} {col_def}")
        raw_conn.commit()

    # Apply configuration from catalog_config.json
    db = SessionLocal()
    try:
        apply_catalog_config(db)
        seed_default_users(db)
    finally:
        db.close()

    print(f"[Database] Initialized with tables: {', '.join(Base.metadata.tables.keys())}")

def seed_default_users(db):
    from auth.security import hash_password
    default_users = [
        {"email": "employee@meridian.com", "name": "Maya Sharma", "role": "employee", "password": "password123"},
        {"email": "maya.sharma@meridian.com", "name": "Maya Sharma", "role": "employee", "password": "password123"},
        {"email": "maya@meridian.com", "name": "Maya Sharma", "role": "employee", "password": "password123"},
        {"email": "customer@meridian.com", "name": "Retail Customer", "role": "customer", "password": "password123"},
        {"email": "alex@meridian.com", "name": "Alex Turner", "role": "support_engineer", "password": "password123"},
    ]
    for u in default_users:
        existing = db.query(User).filter(User.email == u["email"]).first()
        if not existing:
            new_user = User(
                email=u["email"],
                name=u["name"],
                role=u["role"],
                hashed_password=hash_password(u["password"])
            )
            db.add(new_user)
    db.commit()

if __name__ == "__main__":
    init_db()
