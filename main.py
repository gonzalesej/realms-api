"""Create the FastAPI app and connect its route modules."""

import sqlite3

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

from app.database import database_connection, initialize_database
from app.models import (
    Maintenance,
    MaintenanceInput,
    Payment,
    PaymentInput,
    Property,
    PropertyInput,
    Tenant,
    TenantInput,
)

app = FastAPI(title="RealMS - Real Estate Management System API")


@app.exception_handler(sqlite3.IntegrityError)
def handle_integrity_error(request, error):
    """Turn database rule violations (bad property_id, duplicate email) into a 400."""

    return JSONResponse(status_code=400, content={"detail": str(error)})


def found_or_404(record, name):
    if record is None:
        raise HTTPException(status_code=404, detail=f"{name} not found")
    return record


@app.get("/")
def home():
    return {"message": "Welcome to RealMS! Visit /docs to try the API."}


# Properties


@app.get("/properties")
def get_properties():
    result = Property.list_properties(database_connection=database_connection)
    return {"properties": result}


@app.get("/properties/{property_id}")
def get_property(property_id: int):
    result = Property.get_property(
        property_id=property_id, database_connection=database_connection
    )
    return {"property": found_or_404(result, "Property")}


@app.post("/property")
def create_property(property: PropertyInput):
    result = Property.create_property(
        property_input=property, database_connection=database_connection
    )
    return {"property": result}


@app.put("/property/{property_id}")
def edit_property(property_id: int, property: PropertyInput):
    result = Property.update_property(
        property_id=property_id,
        property_input=property,
        database_connection=database_connection,
    )
    return {"property": found_or_404(result, "Property")}


@app.delete("/property/{property_id}")
def delete_property(property_id: int):
    deleted = Property.delete_property(
        property_id=property_id, database_connection=database_connection
    )
    found_or_404(deleted or None, "Property")
    return {"message": "Property deleted successfully"}


# Tenants


@app.get("/tenants")
def get_tenants():
    result = Tenant.list_tenants(database_connection=database_connection)
    return {"tenants": result}


@app.get("/tenants/{tenant_id}")
def get_tenant(tenant_id: int):
    result = Tenant.get_tenant(
        tenant_id=tenant_id, database_connection=database_connection
    )
    return {"tenant": found_or_404(result, "Tenant")}


@app.post("/tenant")
def create_tenant(tenant: TenantInput):
    result = Tenant.create_tenant(
        tenant_input=tenant, database_connection=database_connection
    )
    return {"tenant": result}


@app.put("/tenant/{tenant_id}")
def edit_tenant(tenant_id: int, tenant: TenantInput):
    result = Tenant.update_tenant(
        tenant_id=tenant_id,
        tenant_input=tenant,
        database_connection=database_connection,
    )
    return {"tenant": found_or_404(result, "Tenant")}


@app.delete("/tenant/{tenant_id}")
def delete_tenant(tenant_id: int):
    deleted = Tenant.delete_tenant(
        tenant_id=tenant_id, database_connection=database_connection
    )
    found_or_404(deleted or None, "Tenant")
    return {"message": "Tenant deleted successfully"}


# Payments


@app.get("/payments")
def get_payments():
    result = Payment.list_payments(database_connection=database_connection)
    return {"payments": result}


@app.get("/payments/{payment_id}")
def get_payment(payment_id: int):
    result = Payment.get_payment(
        payment_id=payment_id, database_connection=database_connection
    )
    return {"payment": found_or_404(result, "Payment")}


@app.post("/payment")
def create_payment(payment: PaymentInput):
    result = Payment.create_payment(
        payment_input=payment, database_connection=database_connection
    )
    return {"payment": result}


@app.put("/payment/{payment_id}")
def edit_payment(payment_id: int, payment: PaymentInput):
    result = Payment.update_payment(
        payment_id=payment_id,
        payment_input=payment,
        database_connection=database_connection,
    )
    return {"payment": found_or_404(result, "Payment")}


@app.delete("/payment/{payment_id}")
def delete_payment(payment_id: int):
    deleted = Payment.delete_payment(
        payment_id=payment_id, database_connection=database_connection
    )
    found_or_404(deleted or None, "Payment")
    return {"message": "Payment deleted successfully"}


# Maintenance requests


@app.get("/maintenances")
def get_maintenances():
    result = Maintenance.list_maintenances(database_connection=database_connection)
    return {"maintenances": result}


@app.get("/maintenances/{maintenance_id}")
def get_maintenance(maintenance_id: int):
    result = Maintenance.get_maintenance(
        maintenance_id=maintenance_id, database_connection=database_connection
    )
    return {"maintenance": found_or_404(result, "Maintenance request")}


@app.post("/maintenance")
def create_maintenance(maintenance: MaintenanceInput):
    result = Maintenance.create_maintenance(
        maintenance_input=maintenance, database_connection=database_connection
    )
    return {"maintenance": result}


@app.put("/maintenance/{maintenance_id}")
def edit_maintenance(maintenance_id: int, maintenance: MaintenanceInput):
    result = Maintenance.update_maintenance(
        maintenance_id=maintenance_id,
        maintenance_input=maintenance,
        database_connection=database_connection,
    )
    return {"maintenance": found_or_404(result, "Maintenance request")}


@app.delete("/maintenance/{maintenance_id}")
def delete_maintenance(maintenance_id: int):
    deleted = Maintenance.delete_maintenance(
        maintenance_id=maintenance_id, database_connection=database_connection
    )
    found_or_404(deleted or None, "Maintenance request")
    return {"message": "Maintenance request deleted successfully"}


initialize_database()