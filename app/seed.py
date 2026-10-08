"""Sample records based on the RealMS database of the previous project.

Emails and contact numbers are placeholders so no personal data is published.

The data is only loaded when the properties table is empty, so restarting the
server never creates duplicates. Delete realestate.db to start over.
"""

PROPERTIES = [
    # id, name, type, location, rent_per_month, status
    (9, "Davao Heights", "Residential", "Davao City", 12500, "Occupied"),
    (11, "Matina Grand Residences", "Residential", "Matina, Davao City", 15000, "Occupied"),
    (12, "Toril Garden Homes", "Residential", "Toril, Davao City", 16000, "Occupied"),
    (13, "Mintal Greenview Villas", "Residential", "Mintal, Davao City", 20000, "Occupied"),
    (14, "Ma-a Hillcrest Heights", "Residential", "Ma-a, Davao City", 18000, "Occupied"),
    (15, "Talomo Hillside Terraces", "Residential", "Talomo, Davao City", 19000, "Occupied"),
]

TENANTS = [
    # id, first_name, last_name, email, contact_number, property_id, lease_start, lease_end
    (8, "Renz", "Diaz", "renz.diaz@example.com", "09170000001", 9, "2026-04-21", "2027-02-08"),
    (10, "Beneath", "Lim", "beneath.lim@example.com", "09170000002", 11, "2026-04-27", "2026-06-28"),
    (11, "Soledad", "Paglinawan", "soledad.paglinawan@example.com", "09170000003", 12, "2026-04-27", "2027-08-09"),
    (12, "Ana", "Cruz", "ana.cruz@example.com", "09170000004", 14, "2026-04-28", "2027-12-30"),
    (13, "Jose", "Garcia", "jose.garcia@example.com", "09170000005", 13, "2026-04-28", "2027-05-16"),
    (14, "Zandro", "Villanueva", "zandro.villanueva@example.com", "09170000006", 15, "2026-04-28", "2027-06-10"),
]

PAYMENTS = [
    # id, tenant_id, property_id, amount, type, due_date, payment_date, payment_method, status
    (4, 8, 9, 12500, "Rent", "2026-05-03", "2026-05-03", "Cash", "Paid"),
    (5, 11, 12, 16000, "Rent", "2026-05-01", "2026-05-03", "Online Banking", "Paid"),
    (6, 12, 14, 18000, "Rent", "2026-05-01", "2026-05-04", "Cash", "Paid"),
    (7, 13, 13, 20000, "Rent", "2026-05-01", "2026-05-04", "Cash", "Paid"),
    (9, 10, 11, 15000, "Rent", "2026-05-01", "2026-05-04", "Cash", "Paid"),
    (10, 14, 15, 19000, "Rent", "2026-05-01", "2026-05-04", "Online Banking", "Pending"),
]

MAINTENANCES = [
    # id, tenant_id, property_id, title, description, priority, status, reported_date
    (2, 10, 11, "Toilet Not Flushing",
     "Toilet bowl is not flushing properly. Water rises up when flushed.",
     "Medium", "Pending", "2026-05-03"),
    (4, 11, 12, "Clogged Drain",
     "Bathroom drain is draining very slowly. Water pools up every shower.",
     "Medium", "Pending", "2026-05-03"),
    (5, 12, 14, "Water Heater Not Working",
     "Water heater is not heating up at all. Cold water only since last night.",
     "Medium", "Completed", "2026-05-03"),
    (6, 14, 15, "No Power in Bathroom",
     "Bathroom has no electricity at all. Lights and outlets are completely dead.",
     "Medium", "Pending", "2026-05-03"),
    (16, 12, 14, "Leaking faucet",
     "The kitchen faucet in the unit is leaking and causing water damage to the "
     "cabinet below. Needs immediate repair.",
     "Medium", "Pending", "2026-05-19"),
    (18, 10, 11, "Air conditioning unit not cooling",
     "The air conditioning unit in the bedroom is running but no longer producing "
     "cold air. The room remains hot even after running it for several hours.",
     "Medium", "Pending", "2026-05-19"),
    (19, 8, 9, "Cable wire exposed and damaged",
     "There is an exposed and damaged cable wire running along the wall near the "
     "bathroom. It appears to be an electrical wire and could be a safety hazard "
     "especially when wet.",
     "Medium", "Pending", "2026-05-19"),
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
    connection.executemany(
        "INSERT INTO maintenances (id, tenant_id, property_id, title, description, "
        "priority, status, reported_date) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        MAINTENANCES,
    )
