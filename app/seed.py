from datetime import date, timedelta
from app.services import split_vat


def day(offset):
    """Return the date `offset` days from today as YYYY-MM-DD (negative = past).

    The sample dates are computed from today, so the demo data never looks
    outdated no matter when the project is run.
    """

    return (date.today() + timedelta(days=offset)).isoformat()


PROPERTIES = [
    # id, name, type, location, rent_per_month, status
    (1, "Davao Heights", "Residential", "Davao City", 12500, "Occupied"),
    (
        2,
        "Matina Grand Residences",
        "Residential",
        "Matina, Davao City",
        15000,
        "Occupied",
    ),
    (3, "Toril Garden Homes", "Residential", "Toril, Davao City", 16000, "Occupied"),
    (
        4,
        "Mintal Greenview Villas",
        "Residential",
        "Mintal, Davao City",
        20000,
        "Occupied",
    ),
    (5, "Ma-a Hillcrest Heights", "Residential", "Ma-a, Davao City", 18000, "Occupied"),
    (
        6,
        "Talomo Hillside Terraces",
        "Residential",
        "Talomo, Davao City",
        19000,
        "Occupied",
    ),
    (
        7,
        "Lanang Bayview Residences",
        "Residential",
        "Lanang, Davao City",
        17000,
        "Available",
    ),
]

TENANTS = [
    # id, first_name, last_name, email, contact_number, property_id,
    # lease_start, lease_end
    (1, "Renz", "Diaz", "renz.diaz@example.com", "09170000001", 1, day(-150), day(215)),
    (
        2,
        "Beneath",
        "Lim",
        "beneath.lim@example.com",
        "09170000002",
        2,
        day(-120),
        day(245),
    ),
    (
        3,
        "Soledad",
        "Paglinawan",
        "soledad.paglinawan@example.com",
        "09170000003",
        3,
        day(-100),
        day(265),
    ),
    (4, "Ana", "Cruz", "ana.cruz@example.com", "09170000004", 5, day(-90), day(275)),
    (
        5,
        "Jose",
        "Garcia",
        "jose.garcia@example.com",
        "09170000005",
        4,
        day(-80),
        day(285),
    ),
    (
        6,
        "Zandro",
        "Villanueva",
        "zandro.villanueva@example.com",
        "09170000006",
        6,
        day(-70),
        day(295),
    ),
]

# Rent paid last month on time, one payment due soon (Pending) and one that
# is already late (Overdue). Paying the Overdue one shows the late note.
PAYMENTS = [
    # id, tenant_id, property_id, amount, type, due_date, payment_date,
    # payment_method, status
    (1, 1, 1, 12500, "Rent", day(-40), day(-40), "Cash", "Paid"),
    (2, 3, 3, 16000, "Rent", day(-40), day(-38), "Online Banking", "Paid"),
    (3, 4, 5, 18000, "Rent", day(-40), day(-39), "Cash", "Paid"),
    (4, 5, 4, 20000, "Rent", day(-40), day(-40), "GCash", "Paid"),
    (5, 2, 2, 15000, "Rent", day(-40), day(-37), "Cash", "Paid"),
    (6, 6, 6, 19000, "Rent", day(7), None, None, "Pending"),
    (7, 4, 5, 18000, "Rent", day(-10), None, None, "Overdue"),
]


def seed_database(connection) -> None:
    """Insert the sample records if the database has no properties yet."""

    if connection.execute("SELECT COUNT(*) FROM properties").fetchone()[0] > 0:
        return

    connection.executemany(
        "INSERT INTO properties (id, name, type, location, rent_per_month, status) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        PROPERTIES,
    )
    connection.executemany(
        "INSERT INTO tenants (id, first_name, last_name, email, contact_number, "
        "property_id, lease_start, lease_end) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        TENANTS,
    )
    connection.executemany(
        "INSERT INTO payments (id, tenant_id, property_id, amount, type, due_date, "
        "payment_date, payment_method, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        PAYMENTS,
    )
    # Every payment that is already Paid gets a receipt, exactly as the pay
    # workflow in services.py would have created it.
    receipts = []
    for payment in PAYMENTS:
        payment_id, amount, payment_date, status = (
            payment[0],
            payment[3],
            payment[6],
            payment[8],
        )
        if status == "Paid":
            vat_amount, net_amount = split_vat(amount)
            receipts.append((payment_id, amount, vat_amount, net_amount, payment_date))
    connection.executemany(
        "INSERT INTO transactions (payment_id, amount, vat_amount, net_amount, "
        "created_at) VALUES (?, ?, ?, ?, ?)",
        receipts,
    )
