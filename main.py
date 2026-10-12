import sqlite3

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

from app.database import database_connection, initialize_database
from app.models import (
    PaymentInput,
    PaymentPayInput,
    Property,
    PropertyInput,
    Tenant,
    TenantInput,
    Transaction,
)
from app.services import RentalError, RentalService

app = FastAPI(title="RealMS - Real Estate Management System API")

# One service object that all the workflow routes share.
service = RentalService(database_connection)


@app.exception_handler(sqlite3.IntegrityError)
def handle_integrity_error(request, error):
    """Turn database rule violations (bad property_id, duplicate email) into a 400."""

    return JSONResponse(status_code=400, content={"detail": str(error)})


@app.exception_handler(RentalError)
def handle_rental_error(request, error):
    """Turn a broken business rule from RentalService into an HTTP error."""

    return JSONResponse(
        status_code=error.status_code, content={"detail": error.message}
    )


def found_or_404(record, name):
    """Return the record, or answer with a 404 error if it does not exist."""

    if record is None:
        raise HTTPException(status_code=404, detail=f"{name} not found")
    return record


@app.get("/")
def home():
    """Show a welcome message."""

    return {"message": "Welcome to RealMS! Visit /docs to try the API."}


# Properties


@app.get("/properties")
def get_properties(search: str | None = None):
    """List all properties. Use search to filter by name or location."""

    result = Property.list_properties(
        search=search, database_connection=database_connection
    )
    return {"properties": result}


@app.get("/properties/{property_id}")
def get_property(property_id: int):
    """Show one property."""

    result = Property.get_property(
        property_id=property_id, database_connection=database_connection
    )
    return {"property": found_or_404(result, "Property")}


@app.post("/property")
def create_property(property_data: PropertyInput):
    """Create a property. It starts as Available (or Under Repair)."""

    result = service.create_property(property_input=property_data)
    return {"property": result}


@app.put("/property/{property_id}")
def edit_property(property_id: int, property_data: PropertyInput):
    """Update a property. Occupied is only set by a tenant move-in."""

    result = service.update_property(
        property_id=property_id, property_input=property_data
    )
    return {"property": result}


@app.delete("/property/{property_id}")
def delete_property(property_id: int):
    """Delete a property together with its tenants and payments."""

    deleted = Property.delete_property(
        property_id=property_id, database_connection=database_connection
    )
    found_or_404(deleted or None, "Property")
    return {"message": "Property deleted successfully"}


# Tenants


@app.get("/tenants")
def get_tenants(search: str | None = None):
    """List all tenants. Use search to filter by full name or email."""

    result = Tenant.list_tenants(search=search, database_connection=database_connection)
    return {"tenants": result}


@app.get("/tenants/{tenant_id}")
def get_tenant(tenant_id: int):
    """Show one tenant."""

    result = Tenant.get_tenant(
        tenant_id=tenant_id, database_connection=database_connection
    )
    return {"tenant": found_or_404(result, "Tenant")}


@app.post("/tenant")
def create_tenant(tenant: TenantInput):
    """Move a tenant into an Available property. The property becomes Occupied."""

    result = service.move_in(tenant_input=tenant)
    return {"tenant": result}


@app.put("/tenant/{tenant_id}")
def edit_tenant(tenant_id: int, tenant: TenantInput):
    """Update a tenant's details. Property and status cannot be changed here."""

    result = service.update_tenant(tenant_id=tenant_id, tenant_input=tenant)
    return {"tenant": result}


@app.post("/tenant/{tenant_id}/move-out")
def move_out_tenant(tenant_id: int):
    """End a tenancy. The tenant becomes Inactive and the property Available."""

    result = service.move_out(tenant_id=tenant_id)
    return {"tenant": result}


@app.delete("/tenant/{tenant_id}")
def delete_tenant(tenant_id: int):
    """Delete a tenant and their payments. An Active tenant frees the property."""

    service.delete_tenant(tenant_id=tenant_id)
    return {"message": "Tenant deleted successfully"}


# Payments


@app.get("/payments")
def get_payments():
    """List all payments. Pending payments past their due date show as Overdue."""

    result = service.list_payments()
    return {"payments": result}


@app.get("/payments/{payment_id}")
def get_payment(payment_id: int):
    """Show one payment."""

    result = service.get_payment(payment_id=payment_id)
    return {"payment": found_or_404(result, "Payment")}


@app.post("/payment")
def create_payment(payment: PaymentInput):
    """Record a payment that is due. Its status must be Pending or Overdue."""

    result = service.create_payment(payment_input=payment)
    return {"payment": result}


@app.put("/payment/{payment_id}")
def edit_payment(payment_id: int, payment: PaymentInput):
    """Update a payment that is not paid yet."""

    result = service.update_payment(payment_id=payment_id, payment_input=payment)
    return {"payment": result}


@app.post("/payment/{payment_id}/pay")
def pay_payment(payment_id: int, pay: PaymentPayInput):
    """Pay a payment. This marks it Paid and issues a receipt with the VAT split."""

    result = service.pay_payment(payment_id=payment_id, pay_input=pay)
    return result


@app.delete("/payment/{payment_id}")
def delete_payment(payment_id: int):
    """Delete a payment that is not paid yet."""

    service.delete_payment(payment_id=payment_id)
    return {"message": "Payment deleted successfully"}


# Transactions (receipts). They are created by the pay workflow, so read-only.


@app.get("/transactions")
def get_transactions():
    """List all receipts."""

    result = Transaction.list_transactions(database_connection=database_connection)
    return {"transactions": result}


@app.get("/transactions/{transaction_id}")
def get_transaction(transaction_id: int):
    """Show one receipt."""

    result = Transaction.get_transaction(
        transaction_id=transaction_id, database_connection=database_connection
    )
    return {"transaction": found_or_404(result, "Transaction")}


initialize_database()
# Payments that became late while the server was off are marked Overdue now.
service.mark_overdue_payments()