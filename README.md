# FinTrack (Django + Bootstrap 5)

A clean, user-friendly expense tracker. Tailored to your Excel with **Category** and **Amount (NPR)** columns.

## Quickstart

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install django pandas openpyxl
cd fintrack
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Visit http://127.0.0.1:8000 and register/login.

## Import your Excel
In the UI: **Import** (navbar) → upload `.xlsx` with columns **Category** and **Amount (NPR)**.

Or via management command:
```bash
python manage.py import_excel <your_username> /path/to/Finance_Tracker.xlsx
```

## Features
- Bootstrap 5 dark-glass UI (cool cyan/violet theme)
- Dashboard with doughnut chart by category
- Expense CRUD with search, category filter, pagination
- Category management (with color tags)
- Excel import (Category, Amount (NPR))
- CSV export
- Auth: register/login/logout

## Notes
- Default DB: SQLite (`db.sqlite3`)
- Change `DEBUG`, `ALLOWED_HOSTS`, and `SECRET_KEY` before production.
# expense-tracker
