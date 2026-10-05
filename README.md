# News Application

A Django-based News Application that allows publishers, journalists, editors, and readers to manage and consume news content. The application supports article publication workflows, newsletters, subscriptions, user authentication, and role-based access control.

---

# Features

- User registration and authentication
- Role-based access control
- Article creation and management
- Article approval workflow
- Newsletter management
- Reader subscriptions
- Sphinx-generated documentation
- Docker containerization
- MariaDB database support

---

# Requirements

- Python 3.12+
- MariaDB
- Docker Desktop (optional)
- Git

---

# Installation Using Virtual Environment

## Clone Repository

```bash
git clone https://github.com/dillanpietersen-ops/M07T05.git
cd M07T05
```

## Create Virtual Environment

```bash
python -m venv .venv
```

## Activate Virtual Environment

Windows:

```bash
.venv\Scripts\activate
```

## Install Dependencies

```bash
pip install -r requirements.txt
```

---

# Environment Variables

Create a `.env` file in the project root.

Example:

```env
SECRET_KEY=your_secret_key

DB_NAME=news_application
DB_USER=newsuser
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=3306

EMAIL_HOST_PASSWORD=your_email_password
```

**Important:** Never commit `.env` files, passwords, API keys, or secrets to GitHub.

---

# MariaDB Setup

Create the database:

```sql
CREATE DATABASE news_application;
```

Create a user:

```sql
CREATE USER 'newsuser'@'localhost'
IDENTIFIED BY 'your_password';
```

Grant privileges:

```sql
GRANT ALL PRIVILEGES
ON news_application.*
TO 'newsuser'@'localhost';

FLUSH PRIVILEGES;
```

---

# Database Migrations

Run migrations:

```bash
python manage.py migrate
```

Create a superuser:

```bash
python manage.py createsuperuser
```

---

# Run the Application

```bash
python manage.py runserver
```

Access:

```text
http://127.0.0.1:8000/
```

---

# Sphinx Documentation

Documentation is stored in:

```text
docs/
```

Generate documentation:

```bash
sphinx-build -b html docs/source docs/build/html
```

Open:

```text
docs/build/html/index.html
```

in a browser.

---

# Docker

## Build Docker Image

```bash
docker build -t news_application .
```

## Run With Docker Compose

```bash
docker compose up --build
```

Access:

```text
http://localhost:8001/
```

---

# Project Structure

```text
news_application/
│
├── docs/
├── news/
├── news_application/
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── manage.py
├── .gitignore
└── README.md
```

---

# Security

- Secrets and passwords should be stored in environment variables.
- Do not commit `.env` files.
- Do not publish database credentials or email passwords.

---

# Repository

GitHub Repository:

https://github.com/dillanpietersen-ops/M07T05
