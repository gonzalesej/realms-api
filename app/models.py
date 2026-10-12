"""Pydantic models that validate API input and output. Each class also holds the SQL for its own table."""

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

# Dates are stored as text in the format YYYY-MM-DD.
DATE_PATTERN = r"^\d{4}-\d{2}-\d{2}$"
# A simple email check: something@something.something, without spaces.
EMAIL_PATTERN = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"


def check_real_date(value):
    """Reject dates that match the pattern but do not exist, like 2026-13-45."""

    if value is not None:
        try:
            date.fromisoformat(value)
        except ValueError:
            raise ValueError("must be a real date in the format YYYY-MM-DD")
    return value


def fetch_row(connection, table, record_id):
    """Return one record of a table as a dictionary, or None if it is missing."""

    row = connection.execute(
        f"SELECT * FROM {table} WHERE id = ?", (record_id,)
    ).fetchone()
    return dict(row) if row else None


class PropertyInput(BaseModel):
    """Fields sent when creating or updating a property."""

    name: str = Field(min_length=1)
    type: Literal["Residential", "Commercial"]
    location: str = Field(min_length=1)
    rent_per_month: float = Field(ge=0)
    status: Literal["Available", "Occupied", "Under Repair"] = "Available"

    @staticmethod
    def list_properties(search, database_connection):
        """Return all properties, or those whose name or location has the search."""

        query = "SELECT * FROM properties"
        values = ()
        if search:
            query += " WHERE name LIKE ? OR location LIKE ?"
            values = (f"%{search}%", f"%{search}%")
        with database_connection() as connection:
            rows = connection.execute(query + " ORDER BY id", values).fetchall()
        return [dict(row) for row in rows]

    @staticmethod
    def get_property(property_id, database_connection):
        """Return one property, or None if the id does not exist."""

        with database_connection() as connection:
            return fetch_row(connection, "properties", property_id)

    @staticmethod
    def create_property(property_input, database_connection):
        """Insert a new property and return it."""

        with database_connection() as connection:
            cursor = connection.execute(
                "INSERT INTO properties (name, type, location, rent_per_month, status) "
                "VALUES (?, ?, ?, ?, ?)",
                (
                    property_input.name,
                    property_input.type,
                    property_input.location,
                    property_input.rent_per_month,
                    property_input.status,
                ),
            )
            return fetch_row(connection, "properties", cursor.lastrowid)

    @staticmethod
    def update_property(property_id, property_input, database_connection):
        """Change a property and return it, or None if the id does not exist."""

        with database_connection() as connection:
            connection.execute(
                "UPDATE properties SET name = ?, type = ?, location = ?, "
                "rent_per_month = ?, status = ? WHERE id = ?",
                (
                    property_input.name,
                    property_input.type,
                    property_input.location,
                    property_input.rent_per_month,
                    property_input.status,
                    property_id,
                ),
            )
            return fetch_row(connection, "properties", property_id)

    @staticmethod
    def delete_property(property_id, database_connection):
        """Delete a property. Return True if a row was deleted."""

        with database_connection() as connection:
            cursor = connection.execute(
                "DELETE FROM properties WHERE id = ?", (property_id,)
            )
            return cursor.rowcount > 0


class Property(PropertyInput):
    """A property record returned by the API."""

    id: int


class TenantInput(BaseModel):
    """Fields sent when a tenant moves in or when a tenant is updated."""

    first_name: str = Field(min_length=1)
    last_name: str = Field(min_length=1)
    email: str = Field(pattern=EMAIL_PATTERN)
    contact_number: str | None = None
    property_id: int
    lease_start: str | None = Field(default=None, pattern=DATE_PATTERN)
    lease_end: str | None = Field(default=None, pattern=DATE_PATTERN)
    emergency_contact: str | None = None
    emergency_phone: str | None = None
    status: Literal["Active", "Inactive"] = "Active"

    @field_validator("lease_start", "lease_end")
    @classmethod
    def lease_dates_must_exist(cls, value):
        """Check that the lease dates are real calendar dates."""

        return check_real_date(value)

    @model_validator(mode="after")
    def lease_must_end_after_it_starts(self):
        """Check that the lease does not end before it starts."""

        if self.lease_start and self.lease_end and self.lease_end < self.lease_start:
            raise ValueError("lease_end cannot be earlier than lease_start")
        return self

    @staticmethod
    def list_tenants(search, database_connection):
        """Return all tenants, or those whose full name or email has the search."""

        query = "SELECT * FROM tenants"
        values = ()
        if search:
            query += " WHERE (first_name || ' ' || last_name) LIKE ? OR email LIKE ?"
            values = (f"%{search}%", f"%{search}%")
        with database_connection() as connection:
            rows = connection.execute(query + " ORDER BY id", values).fetchall()
        return [dict(row) for row in rows]

    @staticmethod
    def get_tenant(tenant_id, database_connection):
        """Return one tenant, or None if the id does not exist."""

        with database_connection() as connection:
            return fetch_row(connection, "tenants", tenant_id)

    @staticmethod
    def insert_tenant(connection, tenant_input):
        """Insert a tenant with an already open connection and return the new id.

        The connection is passed in, so the move-in workflow can add the tenant
        and update the property inside one database transaction.
        """

        cursor = connection.execute(
            "INSERT INTO tenants (first_name, last_name, email, contact_number, "
            "property_id, lease_start, lease_end, emergency_contact, "
            "emergency_phone, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                tenant_input.first_name,
                tenant_input.last_name,
                tenant_input.email,
                tenant_input.contact_number,
                tenant_input.property_id,
                tenant_input.lease_start,
                tenant_input.lease_end,
                tenant_input.emergency_contact,
                tenant_input.emergency_phone,
                tenant_input.status,
            ),
        )
        return cursor.lastrowid

    @staticmethod
    def update_tenant(tenant_id, tenant_input, database_connection):
        """Change a tenant and return it, or None if the id does not exist."""

        with database_connection() as connection:
            connection.execute(
                "UPDATE tenants SET first_name = ?, last_name = ?, email = ?, "
                "contact_number = ?, property_id = ?, lease_start = ?, lease_end = ?, "
                "emergency_contact = ?, emergency_phone = ?, status = ? WHERE id = ?",
                (
                    tenant_input.first_name,
                    tenant_input.last_name,
                    tenant_input.email,
                    tenant_input.contact_number,
                    tenant_input.property_id,
                    tenant_input.lease_start,
                    tenant_input.lease_end,
                    tenant_input.emergency_contact,
                    tenant_input.emergency_phone,
                    tenant_input.status,
                    tenant_id,
                ),
            )
            return fetch_row(connection, "tenants", tenant_id)

    @staticmethod
    def delete_tenant(tenant_id, database_connection):
        """Delete a tenant and their records. Return True if a row was deleted."""

        with database_connection() as connection:
            cursor = connection.execute(
                "DELETE FROM tenants WHERE id = ?", (tenant_id,)
            )
            return cursor.rowcount > 0


class Tenant(TenantInput):
    """A tenant record returned by the API."""

    id: int


class PaymentInput(BaseModel):
    """Fields sent when creating or updating a payment."""

    tenant_id: int
    property_id: int
    amount: float = Field(gt=0)
    type: str = Field(default="Rent", min_length=1)
    due_date: str = Field(pattern=DATE_PATTERN)
    payment_date: str | None = Field(default=None, pattern=DATE_PATTERN)
    payment_method: str | None = None
    status: Literal["Paid", "Pending", "Overdue"] = "Pending"
    reference_number: str | None = None
    notes: str | None = None

    @field_validator("due_date", "payment_date")
    @classmethod
    def payment_dates_must_exist(cls, value):
        """Check that the payment dates are real calendar dates."""

        return check_real_date(value)

    @staticmethod
    def list_payments(database_connection):
        """Return all payments."""

        with database_connection() as connection:
            rows = connection.execute("SELECT * FROM payments ORDER BY id").fetchall()
        return [dict(row) for row in rows]

    @staticmethod
    def get_payment(payment_id, database_connection):
        """Return one payment, or None if the id does not exist."""

        with database_connection() as connection:
            return fetch_row(connection, "payments", payment_id)

    @staticmethod
    def create_payment(payment_input, database_connection):
        """Insert a new payment and return it."""

        with database_connection() as connection:
            cursor = connection.execute(
                "INSERT INTO payments (tenant_id, property_id, amount, type, "
                "due_date, payment_date, payment_method, status, reference_number, "
                "notes) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    payment_input.tenant_id,
                    payment_input.property_id,
                    payment_input.amount,
                    payment_input.type,
                    payment_input.due_date,
                    payment_input.payment_date,
                    payment_input.payment_method,
                    payment_input.status,
                    payment_input.reference_number,
                    payment_input.notes,
                ),
            )
            return fetch_row(connection, "payments", cursor.lastrowid)

    @staticmethod
    def update_payment(payment_id, payment_input, database_connection):
        """Change a payment and return it, or None if the id does not exist."""

        with database_connection() as connection:
            connection.execute(
                "UPDATE payments SET tenant_id = ?, property_id = ?, amount = ?, "
                "type = ?, due_date = ?, payment_date = ?, payment_method = ?, "
                "status = ?, reference_number = ?, notes = ? WHERE id = ?",
                (
                    payment_input.tenant_id,
                    payment_input.property_id,
                    payment_input.amount,
                    payment_input.type,
                    payment_input.due_date,
                    payment_input.payment_date,
                    payment_input.payment_method,
                    payment_input.status,
                    payment_input.reference_number,
                    payment_input.notes,
                    payment_id,
                ),
            )
            return fetch_row(connection, "payments", payment_id)

    @staticmethod
    def delete_payment(payment_id, database_connection):
        """Delete a payment and its receipt. Return True if a row was deleted."""

        with database_connection() as connection:
            cursor = connection.execute(
                "DELETE FROM payments WHERE id = ?", (payment_id,)
            )
            return cursor.rowcount > 0


class Payment(PaymentInput):
    """A payment record returned by the API."""

    id: int


class PaymentPayInput(BaseModel):
    """Fields sent when a payment is paid."""

    payment_method: Literal["Cash", "GCash", "Online Banking"]
    reference_number: str | None = None


class Transaction(BaseModel):
    """A receipt that is created when a payment is paid. It is read-only."""

    id: int
    payment_id: int
    amount: float
    vat_amount: float
    net_amount: float
    created_at: str

    @staticmethod
    def list_transactions(database_connection):
        """Return all receipts."""

        with database_connection() as connection:
            rows = connection.execute(
                "SELECT * FROM transactions ORDER BY id"
            ).fetchall()
        return [dict(row) for row in rows]

    @staticmethod
    def get_transaction(transaction_id, database_connection):
        """Return one receipt, or None if the id does not exist."""

        with database_connection() as connection:
            return fetch_row(connection, "transactions", transaction_id)