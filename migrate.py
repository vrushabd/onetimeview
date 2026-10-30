"""
One-shot migration script: adds new columns to the secrets table without
touching existing data. Safe to run multiple times (idempotent).

Usage:
    python migrate.py
"""
from sqlalchemy import text, inspect
from backend.database import engine, Base
import backend.models  # ensure models (Secret, Report) are loaded


def run():
    print("Running database create_all for any missing tables...")
    Base.metadata.create_all(bind=engine)

    inspector = inspect(engine)
    if "secrets" in inspector.get_table_names():
        existing_cols = {c["name"] for c in inspector.get_columns("secrets")}
        print(f"Existing columns in secrets: {existing_cols}")

        additions = {
            "webhook_url": "VARCHAR(500)",
            "cloud_url": "VARCHAR(500)",
            "cloud_public_id": "VARCHAR(255)",
            "cloud_resource_type": "VARCHAR(20)",
        }

        with engine.connect() as conn:
            for col, col_type in additions.items():
                if col not in existing_cols:
                    conn.execute(text(f"ALTER TABLE secrets ADD COLUMN {col} {col_type}"))
                    print(f"  ✅ Added column: secrets.{col} {col_type}")
                else:
                    print(f"  ⏭  Column already exists: secrets.{col}")
            conn.commit()

    print("Migration complete.")


if __name__ == "__main__":
    run()

