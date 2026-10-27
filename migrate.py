"""
One-shot migration script: adds new columns to the secrets table without
touching existing data. Safe to run multiple times (idempotent).

Usage:
    python migrate.py
"""
from sqlalchemy import text, inspect
from backend.database import engine


def run():
    inspector = inspect(engine)
    existing_cols = {c["name"] for c in inspector.get_columns("secrets")}
    print(f"Existing columns: {existing_cols}")

    additions = {
        "webhook_url": "VARCHAR(500)",
    }

    with engine.connect() as conn:
        for col, col_type in additions.items():
            if col not in existing_cols:
                conn.execute(text(f"ALTER TABLE secrets ADD COLUMN {col} {col_type}"))
                print(f"  ✅ Added column: {col} {col_type}")
            else:
                print(f"  ⏭  Column already exists: {col}")
        conn.commit()

    print("Migration complete.")


if __name__ == "__main__":
    run()

