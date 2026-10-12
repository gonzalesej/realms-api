# RealMS - Real Estate Management System API

RealMS is a backend API built with FastAPI and SQLite for managing rental properties. It was built from the FastAPI + SQLite boilerplate of the course.

## The problem

Landlords and property managers often track properties, tenants, and rent payments in spreadsheets, chat messages, and paper receipts. Records get out of date: a property is marked as vacant while a tenant lives in it, and a payment is marked as paid without a receipt.

RealMS keeps all of this in one database and enforces the rules in code, so the records stay consistent with each other.

Intended users: property managers and landlords, who run the system, and the tenants whose move-ins and payments are recorded.

## Features

- Properties, tenants, and payments: create, read, update, and delete for each one.
- Validation: dates must be real, emails must be valid, a lease cannot end before it starts, a payment amount must be above zero, and a payment must belong to the property its tenant rents.
- Search: find properties by name or location, and tenants by name or email.
- Move-in workflow: adding a tenant is only allowed for an Available property, and it marks the property as Occupied in the same transaction.
- Move-out workflow: ending a tenancy makes the tenant Inactive and the property Available again. Deleting an Active tenant frees the property too.
- Pay-rent workflow: paying a payment marks it Paid, records the date and method, and issues a receipt with the VAT breakdown, all in one transaction. A payment made after its due date is noted as late when it is paid. A paid payment is locked: it cannot be edited, paid twice, or deleted on its own (it is only removed if its tenant or property is deleted).
- Automatic Overdue status: a Pending payment whose due date has passed is marked Overdue automatically when the server starts, when payments are read, and when a payment is created or updated.
- Receipts: read-only list of the receipts that were issued.

## Database

Four tables are linked with primary keys and foreign keys. Deleting a parent record removes its child records (ON DELETE CASCADE).

```
properties 1 --- many tenants
tenants    1 --- many payments
properties 1 --- many payments
payments   1 --- 1 transactions (receipts)
```

On the first run the app creates `realestate.db` and loads sample records. The sample dates are computed from today's date, so the data always looks current. Delete `realestate.db` and restart to reset the data.

## Project structure

- `main.py` creates the FastAPI app and defines the routes.
- `app/database.py` opens SQLite connections and creates the tables.
- `app/models.py` holds the Pydantic classes. Each class also holds the SQL queries of its table.
- `app/services.py` holds `RentalService`, the class that runs the workflows that touch more than one table.
- `app/seed.py` holds the sample records.

## OOP in this project

- Classes and inheritance: `PropertyInput` describes the fields sent by a client, and `Property` extends it with an `id`. The same pattern is used for tenants and payments.
- Encapsulation: each model class keeps the SQL of its own table, and `RentalService` keeps the business rules, the queries that touch more than one table, and the database connection function it was created with.
- Separation of responsibilities: routes handle requests, models handle one table, and the service handles workflows.
- Custom exception: `RentalError` represents a broken business rule, and `main.py` turns it into an HTTP error.

## Run it on Windows

From this folder, create and activate a virtual environment, then install the dependencies:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m uvicorn main:app --reload
```

Then open <http://127.0.0.1:8000/docs> in your browser. The API docs page lets you try every endpoint.

## Endpoints

| Method and path | Purpose |
| --- | --- |
| `GET /` | Welcome message |
| `GET /properties` | List properties (`?search=` filters by name or location) |
| `GET /properties/{property_id}` | Show one property |
| `POST /property` | Create a property |
| `PUT /property/{property_id}` | Update a property (Occupied is only set by a move-in) |
| `DELETE /property/{property_id}` | Delete a property with its tenants and payments |
| `GET /tenants` | List tenants (`?search=` filters by name or email) |
| `GET /tenants/{tenant_id}` | Show one tenant |
| `POST /tenant` | Move a tenant into an Available property |
| `PUT /tenant/{tenant_id}` | Update a tenant's details |
| `POST /tenant/{tenant_id}/move-out` | End a tenancy |
| `DELETE /tenant/{tenant_id}` | Delete a tenant and their payments (frees the property if Active) |
| `GET /payments` | List payments (late Pending payments are marked Overdue first) |
| `GET /payments/{payment_id}` | Show one payment |
| `POST /payment` | Record a payment that is due (must match the tenant's property) |
| `PUT /payment/{payment_id}` | Update a payment that is not paid yet |
| `POST /payment/{payment_id}/pay` | Pay a payment and issue a receipt |
| `DELETE /payment/{payment_id}` | Delete a payment that is not paid yet |
| `GET /transactions` | List receipts |
| `GET /transactions/{transaction_id}` | Show one receipt |

## Try the workflows

1. Pay rent: in `/docs`, open `POST /payment/{payment_id}/pay`, use payment `6` (due in 7 days) and send `{"payment_method": "GCash"}`. Then open `GET /transactions` to see the new receipt. Payment `7` is already overdue, so paying it adds the note "Paid N day(s) late." to the payment.
2. Move in: property `7` is the only Available sample property. Use `POST /tenant` with `"property_id": 7`, and the property becomes Occupied. You can also create more properties with `POST /property`.
3. Move out: use `POST /tenant/{tenant_id}/move-out`. The property becomes Available again.