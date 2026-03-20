# REMS Test Suite

This directory contains 23 automated test cases for the Retail Estate Management System (REMS), written with **pytest** and Flask's built-in test client. All tests run against an **in-memory SQLite database**, so no external database setup is required. Run in virtual environment if using one.

## Prerequisites

- **Python 3.8+**
- All project dependencies installed (see below)

## Setup

1. From the project root, install dependencies:

   ```bash
   pip install -r src/requirements.txt
   ```

2. Verify pytest is available:

   ```bash
   pytest --version
   ```

## Running the Tests

All commands should be run from the **tests** directory.

```bash
cd tests
```

### Run all tests

```bash
python -m pytest -v
```

### Run a single test file

```bash
python -m pytest -v test_tc006_login.py
```

### Run a specific test function

```bash
python -m pytest -v test_tc006_login.py::test_successful_login
```

### Run tests matching a keyword

```bash
python -m pytest -v -k "appointment"
```

## Test Case Overview

| Test File | Description | Category |
|---|---|---|
| `test_tc001_search_price_filter.py` | Store unit search by max price filter | Functional |
| `test_tc002_appointment_conflict.py` | Double-booking prevention for appointments | Functional |
| `test_tc003_submit_rental_application.py` | Submit rental application with documents | Functional |
| `test_tc004_add_store_unit.py` | Add a new store unit record | Functional |
| `test_tc005_calculate_bill.py` | Monthly bill calculation (rent + utilities - discounts) | Functional |
| `test_tc006_login.py` | User login with valid and invalid credentials | Functional |
| `test_tc007_sign_unapproved_lease.py` | Signing a lease that is not yet fully approved | Functional |
| `test_tc008_rbac_units.py` | Role-based access control on store units | Security |
| `test_tc009_search_response_time.py` | Search response time with 1,000+ records | Performance |
| `test_tc010_input_validation.py` | XSS / special character input sanitization | Security |
| `test_tc011_delete_confirmation.py` | Delete confirmation dialog behavior | UI / UX |
| `test_tc012_browser_consistency.py` | Cross-browser layout consistency (Bootstrap 5) | Compatibility |
| `test_tc013_mobile_responsive.py` | Responsive design at mobile viewport (375px) | Compatibility |
| `test_tc014_search_load.py` | Search response time under repeated load | Performance |
| `test_tc015_appointment_slot_perf.py` | Appointment slot lookup with 200+ records | Performance |
| `test_tc016_conflict_check_perf.py` | Conflict detection with 500+ appointments | Performance |
| `test_tc017_billing_batch_perf.py` | Batch billing for 100 tenants within 10 seconds | Performance |
| `test_tc018_db_query_index.py` | Search query uses database indexes (MySQL only) | Performance |
| `test_tc019_large_result_set.py` | UI responsiveness with 200+ results | Performance |
| `test_tc020_overdue_notification.py` | Overdue payment notification generation | Functional |
| `test_tc021_misuse_charges.py` | Apply charges for misused maintenance requests | Functional |
| `test_tc022_escalation.py` | Maintenance request priority ordering | Functional |
| `test_tc023_payment_cycle_billing.py` | Invoice calculation by payment cycle | Functional |

## Test Architecture

- **`conftest.py`** — Shared fixtures used across all tests:
  - `app` — Creates a Flask app configured for testing with an in-memory SQLite database
  - `setup_db` — Creates tables before each test and drops them after (auto-use)
  - `client` — Flask test client for making HTTP requests
  - `db_session` — Direct database session access
  - `seed_users` — Pre-populates an Admin, Leasing Agent, and Tenant user
  - `seed_mall` — Pre-populates a test mall
  - `seed_units` — Pre-populates three store units at different price points
  - `login` / `login_as_admin` / `login_as_agent` / `login_as_tenant` — Helper functions to authenticate as different roles

## Notes

- **TC-018** (`test_tc018_db_query_index.py`) requires a live MySQL connection and will be skipped automatically when running against SQLite.
- Performance tests seed large amounts of data and may take longer than functional tests. To skip them:
  ```bash
  python -m pytest -v --ignore=test_tc009_search_response_time.py --ignore=test_tc014_search_load.py --ignore=test_tc015_appointment_slot_perf.py --ignore=test_tc016_conflict_check_perf.py --ignore=test_tc017_billing_batch_perf.py --ignore=test_tc018_db_query_index.py --ignore=test_tc019_large_result_set.py
  ```
