import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from app.seed import seed_database

DATABASE_FILE = Path(__file__).resolve().parent.parent / "realestate.db"


@contextmanager
def database_connection() -> Iterator[sqlite3.Connection]:
    """Open a database connection and always close it after the operation.

    The work done inside the `with` block is one transaction: it is committed
    when the block ends normally and rolled back if an error is raised.
    """

    connection = sqlite3.connect(DATABASE_FILE)
    connection.row_factory = sqlite3.Row
    # SQLite ignores foreign keys unless this is switched on for every connection.
    connection.execute("PRAGMA foreign_keys = ON")
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def initialize_database() -> None:
    """Create the tables the first time the app runs and load the sample data.

    Relationships between the tables:
        properties 1 --- * tenants        (a tenant lives in one property)
        tenants    1 --- * payments       (a tenant makes many payments)
        properties 1 --- * payments       (a payment is for one property)
        payments   1 --- 1 transactions   (a paid payment has one receipt)
    ON DELETE CASCADE removes the child records when a parent record is deleted.
    """

    with database_connection() as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS properties (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                type TEXT NOT NULL CHECK (type IN ('Residential', 'Commercial')),
                location TEXT NOT NULL,
                rent_per_month REAL NOT NULL CHECK (rent_per_month >= 0),
                status TEXT NOT NULL DEFAULT 'Available'
                    CHECK (status IN ('Available', 'Occupied', 'Under Repair'))
            );

            CREATE TABLE IF NOT EXISTS tenants (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                first_name TEXT NOT NULL,
                last_name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE COLLATE NOCASE,
                contact_number TEXT,
                property_id INTEGER NOT NULL,
                lease_start TEXT,
                lease_end TEXT,
                emergency_contact TEXT,
                emergency_phone TEXT,
                status TEXT NOT NULL DEFAULT 'Active'
                    CHECK (status IN ('Active', 'Inactive')),
                FOREIGN KEY (property_id) REFERENCES properties (id)
                    ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tenant_id INTEGER NOT NULL,
                property_id INTEGER NOT NULL,
                amount REAL NOT NULL CHECK (amount >= 0),
                type TEXT NOT NULL DEFAULT 'Rent',
                due_date TEXT NOT NULL,
                payment_date TEXT,
                payment_method TEXT,
                status TEXT NOT NULL DEFAULT 'Pending'
                    CHECK (status IN ('Paid', 'Pending', 'Overdue')),
                reference_number TEXT,
                notes TEXT,
                FOREIGN KEY (tenant_id) REFERENCES tenants (id)
                    ON DELETE CASCADE,
                FOREIGN KEY (property_id) REFERENCES properties (id)
                    ON DELETE CASCADE
            );

            -- Receipts. A row is added only by the pay workflow. UNIQUE makes
            -- sure one payment can never receive two receipts.
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                payment_id INTEGER NOT NULL UNIQUE,
                amount REAL NOT NULL CHECK (amount >= 0),
                vat_amount REAL NOT NULL CHECK (vat_amount >= 0),
                net_amount REAL NOT NULL CHECK (net_amount >= 0),
                created_at TEXT NOT NULL DEFAULT (date('now')),
                FOREIGN KEY (payment_id) REFERENCES payments (id)
                    ON DELETE CASCADE
            );
            """
        )
        seed_database(connection)
