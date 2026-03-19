# REMS - Quick Start Guide

## Prerequisites

- **Python 3.10+** — [Download](https://www.python.org/downloads/)
- **MySQL 8.0+** — [Download](https://dev.mysql.com/downloads/mysql/)
- **Git** — for cloning the repo
- A code editor (VS Code recommended)

## Step 1: Clone the Repository

```bash
git clone https://github.com/eamontryan/digt3101_team3
cd digt3101_team3
```

## Step 2: Set Up the Database

1. Open MySQL Workbench or a MySQL terminal
2. Run the schema file to create the database and seed sample data:
```bash
mysql -u root -p < src/REMS_schema.sql
```
3. Verify the database was created:
```sql
USE rems_db;
SHOW TABLES;
```
You should see all 14 tables listed.

## Step 3: Set Up the Python Environment

```bash
# Navigate to the source directory
cd src

# Create a virtual environment
python -m venv venv

# Activate it
# On Windows (Command Prompt):
venv\Scripts\activate
# On Windows (PowerShell):
venv\Scripts\Activate.ps1
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Step 4: Configure Environment Variables

Create a `.env` file in the `src/` directory:

```env
# Database connection
DATABASE_URL=mysql+pymysql://root:yourpassword@localhost:3306/rems_db

# Flask secret key (used for session cookies and CSRF protection)
SECRET_KEY=change-this-to-a-random-string

# File upload directory
UPLOAD_FOLDER=uploads

# Flask environment
FLASK_ENV=development
FLASK_DEBUG=1
```

Replace `yourpassword` with your actual MySQL root password. If you use a different MySQL user, update accordingly.

## Step 5: Run the Application

```bash
flask run --debug
```

The app will start at **http://localhost:5000**

## Step 6: Log In with Sample Users

The schema seeds these test accounts (all the passwords are password123):

| Role | Username | Name |
|------|----------|------|
| **Dev** | `dev_admin` | Dev User |
| Admin | `admin_john` | John Carter |
| Admin | `admin_sarah` | Sarah Mitchell |
| Leasing Agent | `agent_mike` | Mike Torres |
| Leasing Agent | `agent_lisa` | Lisa Reyes |
| Leasing Agent | `agent_david` | David Chen |
| Tenant | `tenant_anna` | Anna Lopez |
| Tenant | `tenant_brian` | Brian Santos |
| Tenant | `tenant_carla` | Carla Mendoza |
| Tenant | `tenant_derek` | Derek Villanueva |
| Tenant | `tenant_elena` | Elena Cruz |

> **Dev account:** The `dev_admin` user can switch between Admin, Leasing Agent, and Tenant views using the role switcher in the navbar. This is the only account with this capability and is intended for development and testing purposes.

## Common Commands

```bash
# Start the dev server
flask run --debug

# Install a new package and save it
pip install <package-name>
pip freeze > requirements.txt

# Deactivate the virtual environment when done
deactivate
```

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `ModuleNotFoundError: No module named 'flask'` | Make sure your virtual environment is activated (`venv\Scripts\activate`) |
| `Access denied for user 'root'@'localhost'` | Check your MySQL password in `.env` |
| `Can't connect to MySQL server` | Make sure MySQL service is running |
| `Port 5000 already in use` | Run with a different port: `flask run --port 5001` |
| `TemplateNotFound` | Make sure you're running `flask run` from the `src/` directory |

## Project Structure Overview

```
src/
├── app.py                 # App entry point
├── config.py              # Configuration (reads .env)
├── requirements.txt       # Python dependencies
├── .env                   # Local environment variables (do NOT commit)
├── models/                # SQLAlchemy models (1 per DB table)
├── routes/                # URL route handlers (grouped by feature)
├── services/              # Business logic layer
├── templates/             # Jinja2 HTML templates + Bootstrap 5
├── static/                # CSS, JS, images
└── uploads/               # User-uploaded files (gitignored)
```
