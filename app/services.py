from datetime import date
from app.models import Payment, Property, Tenant, TenantInput, fetch_row

# Philippine VAT of 12 percent. Rents are treated as VAT-inclusive amounts.
VAT_RATE = 0.12


class RentalError(Exception):
    """A business rule was broken. main.py turns it into an HTTP error."""

    def __init__(self, message, status_code=400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def split_vat(amount):
    """Split a VAT-inclusive amount into its VAT part and its net part."""

    vat_amount = round(amount * VAT_RATE / (1 + VAT_RATE), 2)
    return vat_amount, round(amount - vat_amount, 2)


class RentalService:
    """The workflows of the RealMS system.

    The object keeps the database_connection function it was created with, so
    every method opens its own connection through it. Everything done inside one
    `with self.database_connection()` block is a single transaction: it is
    committed when the block ends and rolled back if an error is raised.
    """

    def __init__(self, database_connection):
        self.database_connection = database_connection

    # Property rules

    def create_property(self, property_input):
        """Add a property. It cannot start as Occupied, only a move-in does that."""

        if property_input.status == "Occupied":
            raise RentalError("A property becomes Occupied when a tenant moves in.")
        return Property.create_property(
            property_input=property_input, database_connection=self.database_connection
        )

    def update_property(self, property_id, property_input):
        """Edit a property while keeping its status in line with its tenants."""

        with self.database_connection() as connection:
            current = fetch_row(connection, "properties", property_id)
            if current is None:
                raise RentalError("Property not found", 404)
            has_active_tenant = connection.execute(
                "SELECT 1 FROM tenants WHERE property_id = ? AND status = 'Active'",
                (property_id,),
            ).fetchone()
        # Rules: Occupied is set only by a move-in, and a property with an
        # Active tenant stays Occupied until that tenant moves out.
        if property_input.status == "Occupied" and current["status"] != "Occupied":
            raise RentalError("A property becomes Occupied when a tenant moves in.")
        if has_active_tenant and property_input.status != "Occupied":
            raise RentalError(
                "This property has an Active tenant. Move the tenant out first."
            )
        return Property.update_property(
            property_id=property_id,
            property_input=property_input,
            database_connection=self.database_connection,
        )

    # Tenant workflows

    def move_in(self, tenant_input):
        """Add a tenant and mark the property as Occupied, as one transaction."""

        if tenant_input.status != "Active":
            raise RentalError("A tenant who moves in must be Active.")
        with self.database_connection() as connection:
            rented_property = fetch_row(
                connection, "properties", tenant_input.property_id
            )
            if rented_property is None:
                raise RentalError("Property not found", 404)
            # Rule: only an Available property can receive a new tenant.
            if rented_property["status"] != "Available":
                raise RentalError(
                    f"Property is {rented_property['status']}, so nobody can move in."
                )
            tenant_id = TenantInput.insert_tenant(connection, tenant_input)
            connection.execute(
                "UPDATE properties SET status = 'Occupied' WHERE id = ?",
                (tenant_input.property_id,),
            )
            return fetch_row(connection, "tenants", tenant_id)

    def move_out(self, tenant_id):
        """End a tenancy: the tenant becomes Inactive and the property Available."""

        with self.database_connection() as connection:
            tenant = fetch_row(connection, "tenants", tenant_id)
            if tenant is None:
                raise RentalError("Tenant not found", 404)
            if tenant["status"] == "Inactive":
                raise RentalError("Tenant has already moved out.")
            connection.execute(
                "UPDATE tenants SET status = 'Inactive' WHERE id = ?", (tenant_id,)
            )
            # Only free the property if it is still marked as Occupied.
            connection.execute(
                "UPDATE properties SET status = 'Available' "
                "WHERE id = ? AND status = 'Occupied'",
                (tenant["property_id"],),
            )
            return fetch_row(connection, "tenants", tenant_id)

    def update_tenant(self, tenant_id, tenant_input):
        """Edit a tenant's details without breaking the property status."""

        current = Tenant.get_tenant(
            tenant_id=tenant_id, database_connection=self.database_connection
        )
        if current is None:
            raise RentalError("Tenant not found", 404)
        # Rules: property and status only change through move-in and move-out.
        if current["property_id"] != tenant_input.property_id:
            raise RentalError(
                "A tenant cannot be moved to another property. "
                "Move the tenant out and add a new move-in."
            )
        if current["status"] != tenant_input.status:
            raise RentalError(
                "Use the move-out endpoint to end a tenancy. "
                "A tenant who moved out needs a new move-in."
            )
        return Tenant.update_tenant(
            tenant_id=tenant_id,
            tenant_input=tenant_input,
            database_connection=self.database_connection,
        )

    def delete_tenant(self, tenant_id):
        """Delete a tenant and free the property if the tenant was still Active."""

        with self.database_connection() as connection:
            tenant = fetch_row(connection, "tenants", tenant_id)
            if tenant is None:
                raise RentalError("Tenant not found", 404)
            if tenant["status"] == "Active":
                connection.execute(
                    "UPDATE properties SET status = 'Available' "
                    "WHERE id = ? AND status = 'Occupied'",
                    (tenant["property_id"],),
                )
            # The tenant's payments and receipts are removed by ON DELETE CASCADE.
            connection.execute("DELETE FROM tenants WHERE id = ?", (tenant_id,))

    # Payment workflows

    def mark_overdue_payments(self):
        """Mark every Pending payment whose due date has passed as Overdue.

        A payment due today is still Pending. It becomes Overdue the day after.
        """

        with self.database_connection() as connection:
            connection.execute(
                "UPDATE payments SET status = 'Overdue' "
                "WHERE status = 'Pending' AND due_date < ?",
                (date.today().isoformat(),),
            )

    def list_payments(self):
        """Return all payments, after late Pending payments become Overdue."""

        self.mark_overdue_payments()
        return Payment.list_payments(database_connection=self.database_connection)

    def get_payment(self, payment_id):
        """Return one payment (or None), after late Pending payments become Overdue."""

        self.mark_overdue_payments()
        return Payment.get_payment(
            payment_id=payment_id, database_connection=self.database_connection
        )

    def check_tenant_owns_property(self, payment_input):
        """Make sure the payment's property is the one the tenant lives in."""

        tenant = Tenant.get_tenant(
            tenant_id=payment_input.tenant_id,
            database_connection=self.database_connection,
        )
        if tenant is None:
            raise RentalError("Tenant not found", 404)
        if tenant["property_id"] != payment_input.property_id:
            raise RentalError("This tenant does not rent that property.")

    def create_payment(self, payment_input):
        """Record a payment that is still due. It is paid through pay_payment."""

        if payment_input.status == "Paid":
            raise RentalError(
                "Create the payment as Pending or Overdue, "
                "then pay it with the pay endpoint."
            )
        self.check_tenant_owns_property(payment_input)
        created = Payment.create_payment(
            payment_input=payment_input, database_connection=self.database_connection
        )
        # A payment recorded with a past due date is Overdue right away.
        self.mark_overdue_payments()
        return Payment.get_payment(
            payment_id=created["id"], database_connection=self.database_connection
        )

    def update_payment(self, payment_id, payment_input):
        """Edit a payment that is not paid yet."""

        current = Payment.get_payment(
            payment_id=payment_id, database_connection=self.database_connection
        )
        if current is None:
            raise RentalError("Payment not found", 404)
        # Rules: a paid payment has a receipt, so it is locked, and only the
        # pay endpoint is allowed to mark a payment as Paid.
        if current["status"] == "Paid":
            raise RentalError("A paid payment cannot be edited.")
        if payment_input.status == "Paid":
            raise RentalError("Use the pay endpoint to mark a payment as Paid.")
        self.check_tenant_owns_property(payment_input)
        Payment.update_payment(
            payment_id=payment_id,
            payment_input=payment_input,
            database_connection=self.database_connection,
        )
        self.mark_overdue_payments()
        return Payment.get_payment(
            payment_id=payment_id, database_connection=self.database_connection
        )

    def delete_payment(self, payment_id):
        """Delete a payment that is not paid. A paid payment has a receipt."""

        payment = Payment.get_payment(
            payment_id=payment_id, database_connection=self.database_connection
        )
        if payment is None:
            raise RentalError("Payment not found", 404)
        if payment["status"] == "Paid":
            raise RentalError("A paid payment and its receipt cannot be deleted.")
        Payment.delete_payment(
            payment_id=payment_id, database_connection=self.database_connection
        )

    def pay_payment(self, payment_id, pay_input):
        """Pay a payment and issue its receipt, as one transaction.

        Three things happen together: the payment becomes Paid, it gets a date
        and a method, and a row with the VAT breakdown is added to transactions.
        If any step fails, none of them is saved.
        """

        with self.database_connection() as connection:
            payment = fetch_row(connection, "payments", payment_id)
            if payment is None:
                raise RentalError("Payment not found", 404)
            if payment["status"] == "Paid":
                raise RentalError("Payment is already paid.")
            today = date.today().isoformat()
            # Rule: a payment made after its due date is recorded as late.
            days_late = (date.today() - date.fromisoformat(payment["due_date"])).days
            notes = payment["notes"]
            if days_late > 0:
                late_note = f"Paid {days_late} day(s) late."
                notes = f"{notes} {late_note}" if notes else late_note
            connection.execute(
                "UPDATE payments SET status = 'Paid', payment_date = ?, "
                "payment_method = ?, reference_number = ?, notes = ? WHERE id = ?",
                (
                    today,
                    pay_input.payment_method,
                    pay_input.reference_number,
                    notes,
                    payment_id,
                ),
            )
            vat_amount, net_amount = split_vat(payment["amount"])
            cursor = connection.execute(
                "INSERT INTO transactions (payment_id, amount, vat_amount, "
                "net_amount, created_at) VALUES (?, ?, ?, ?, ?)",
                (payment_id, payment["amount"], vat_amount, net_amount, today),
            )
            return {
                "payment": fetch_row(connection, "payments", payment_id),
                "transaction": fetch_row(connection, "transactions", cursor.lastrowid),
            }