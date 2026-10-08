"""Data models used to validate API input and output."""

from typing import Literal

from pydantic import BaseModel, Field

DATE_PATTERN = r"^\d{4}-\d{2}-\d{2}$"


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
    status: Literal["Available", "Occupied", "Maintenance"] = "Available"

    @staticmethod
    def list_properties(database_connection):
        with database_connection() as connection:
            rows = connection.execute(
                "SELECT * FROM properties ORDER BY id"
            ).fetchall()
        return [dict(row) for row in rows]

    @staticmethod
    def get_property(property_id, database_connection):
        with database_connection() as connection:
            return fetch_row(connection, "properties", property_id)

    @staticmethod
    def create_property(property_input, database_connection):
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
        with database_connection() as connection:
            cursor = connection.execute(
                "DELETE FROM properties WHERE id = ?", (property_id,)
            )
            return cursor.rowcount > 0


class Property(PropertyInput):
    """A property record returned by the API."""

    id: int


class TenantInput(BaseModel):
    """Fields sent when creating or updating a tenant."""

    first_name: str = Field(min_length=1)
    last_name: str = Field(min_length=1)
    email: str = Field(min_length=3)
    contact_number: str | None = None
    property_id: int
    lease_start: str | None = Field(default=None, pattern=DATE_PATTERN)
    lease_end: str | None = Field(default=None, pattern=DATE_PATTERN)
    emergency_contact: str | None = None
    emergency_phone: str | None = None
    status: Literal["Active", "Inactive"] = "Active"

    @staticmethod
    def list_tenants(database_connection):
        with database_connection() as connection:
            rows = connection.execute(
                "SELECT * FROM tenants ORDER BY id"
            ).fetchall()
        return [dict(row) for row in rows]

    @staticmethod
    def get_tenant(tenant_id, database_connection):
        with database_connection() as connection:
            return fetch_row(connection, "tenants", tenant_id)

    @staticmethod
    def create_tenant(tenant_input, database_connection):
        with database_connection() as connection:
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
            return fetch_row(connection, "tenants", cursor.lastrowid)

    @staticmethod
    def update_tenant(tenant_id, tenant_input, database_connection):
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
    amount: float = Field(ge=0)
    type: str = Field(default="Rent", min_length=1)
    due_date: str = Field(pattern=DATE_PATTERN)
    payment_date: str | None = Field(default=None, pattern=DATE_PATTERN)
    payment_method: str | None = None
    status: Literal["Paid", "Pending", "Overdue"] = "Pending"
    reference_number: str | None = None
    notes: str | None = None

    @staticmethod
    def list_payments(database_connection):
        with database_connection() as connection:
            rows = connection.execute(
                "SELECT * FROM payments ORDER BY id"
            ).fetchall()
        return [dict(row) for row in rows]

    @staticmethod
    def get_payment(payment_id, database_connection):
        with database_connection() as connection:
            return fetch_row(connection, "payments", payment_id)

    @staticmethod
    def create_payment(payment_input, database_connection):
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
        with database_connection() as connection:
            cursor = connection.execute(
                "DELETE FROM payments WHERE id = ?", (payment_id,)
            )
            return cursor.rowcount > 0


class Payment(PaymentInput):
    """A payment record returned by the API."""

    id: int


class MaintenanceInput(BaseModel):
    """Fields sent when creating or updating a maintenance request."""

    tenant_id: int
    property_id: int
    title: str = Field(min_length=1)
    description: str = Field(min_length=1)
    priority: Literal["Low", "Medium", "High", "Emergency"] = "Medium"
    status: Literal["Pending", "In Progress", "Completed", "Cancelled"] = "Pending"
    cost: float | None = Field(default=None, ge=0)
    scheduled_date: str | None = Field(default=None, pattern=DATE_PATTERN)

    @staticmethod
    def list_maintenances(database_connection):
        with database_connection() as connection:
            rows = connection.execute(
                "SELECT * FROM maintenances ORDER BY id"
            ).fetchall()
        return [dict(row) for row in rows]

    @staticmethod
    def get_maintenance(maintenance_id, database_connection):
        with database_connection() as connection:
            return fetch_row(connection, "maintenances", maintenance_id)

    @staticmethod
    def create_maintenance(maintenance_input, database_connection):
        with database_connection() as connection:
            cursor = connection.execute(
                "INSERT INTO maintenances (tenant_id, property_id, title, "
                "description, priority, status, cost, scheduled_date) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    maintenance_input.tenant_id,
                    maintenance_input.property_id,
                    maintenance_input.title,
                    maintenance_input.description,
                    maintenance_input.priority,
                    maintenance_input.status,
                    maintenance_input.cost,
                    maintenance_input.scheduled_date,
                ),
            )
            return fetch_row(connection, "maintenances", cursor.lastrowid)

    @staticmethod
    def update_maintenance(maintenance_id, maintenance_input, database_connection):
        with database_connection() as connection:
            connection.execute(
                "UPDATE maintenances SET tenant_id = ?, property_id = ?, title = ?, "
                "description = ?, priority = ?, status = ?, cost = ?, "
                "scheduled_date = ? WHERE id = ?",
                (
                    maintenance_input.tenant_id,
                    maintenance_input.property_id,
                    maintenance_input.title,
                    maintenance_input.description,
                    maintenance_input.priority,
                    maintenance_input.status,
                    maintenance_input.cost,
                    maintenance_input.scheduled_date,
                    maintenance_id,
                ),
            )
            return fetch_row(connection, "maintenances", maintenance_id)

    @staticmethod
    def delete_maintenance(maintenance_id, database_connection):
        with database_connection() as connection:
            cursor = connection.execute(
                "DELETE FROM maintenances WHERE id = ?", (maintenance_id,)
            )
            return cursor.rowcount > 0


class Maintenance(MaintenanceInput):
    """A maintenance request record returned by the API."""

    id: int
    reported_date: str