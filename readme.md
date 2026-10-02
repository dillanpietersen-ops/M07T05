---

# AuthLog Django Project

This is a Django web application project that includes two main apps:

* **grabsomore**: Handles user authentication, registration, password reset, and user sessions.
* **eCommerce**: Basic eCommerce functionality with products, permissions, and a shopping cart.

---

## Table of Contents

- [Table of Contents](#table-of-contents)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Database Setup](#database-setup)
- [Running the Project](#running-the-project)
- [Usage](#usage)
- [Password Reset Testing](#password-reset-testing)
- [Troubleshooting](#troubleshooting)
- [Project Structure](#project-structure)

---

## Prerequisites

Before you begin, ensure you have met the following requirements:

* Python 3.9 or later installed. [Download Python](https://www.python.org/downloads/)
* MySQL installed and running on your machine.
* Basic knowledge of using the command line / terminal.
* Git installed to clone the repository (optional but recommended).

---

## Installation

1. **Clone the repository** (or download the ZIP and extract):

   ```bash
   git clone https://github.com/yourusername/AuthLog.git
   cd AuthLog
   ```

2. **Create and activate a virtual environment** (recommended):

   * On Windows:

     ```bash
     python -m venv venv
     venv\Scripts\activate
     ```
   * On macOS/Linux:

     ```bash
     python3 -m venv venv
     source venv/bin/activate
     ```

3. **Install the required Python packages:**

   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Email Settings:**

   For sending emails (like password resets), update your email credentials in `AuthLog/settings.py` under the email section:

   ```python
   EMAIL_HOST_USER = 'your-email@example.com'
   EMAIL_HOST_PASSWORD = 'your-email-password-or-app-password'
   ```

   > **Note:** For Gmail, you might need to create an App Password and enable "Less secure app access".

---

## Database Setup

1. **Create MySQL database:**

   Login to your MySQL server and create the database:

   ```sql
   CREATE DATABASE ecommerce_db;
   ```

2. **Update database credentials in `AuthLog/settings.py`** if your MySQL username or password differ:

   ```python
   DATABASES = {
       'default': {
           'ENGINE': 'django.db.backends.mysql',
           'NAME': 'ecommerce_db',
           'USER': 'root',
           'PASSWORD': 'your_mysql_password',
           'HOST': 'localhost',
           'PORT': '',
       }
   }
   ```

3. **Install MySQL Python adapter** if not already installed:

   ```bash
   pip install mysqlclient
   ```

---

## Running the Project

1. **Apply migrations:**

   Run the following commands to create the necessary database tables:

   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

2. **Create a superuser** (for admin / vendor access):

   ```bash
   python manage.py createsuperuser
   ```

   Follow the prompts to create a user with admin privileges.

3. **Run the development server:**

   ```bash
   python manage.py runserver
   ```

4. **Access the application:**

   * Open your browser and go to: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
   * You can login, register new users, browse products, and test password reset functionality.

---

## Usage

* **Authentication (`grabsomore` app):**

  * Login at `/` (root URL)
  * Register at `/register/`
  * Request password reset at `/request-password-reset/`
  * Reset password via emailed token link

* **eCommerce (`eCommerce` app):**

  * View all products at `/` (root URL, depending on project URL setup)
  * View product details, change prices (if authorized), add to cart, and view cart.

---

## Password Reset Testing

If you want to test password reset functionality without sending real emails:

1. Change email backend in `AuthLog/settings.py` to console:

   ```python
   EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
   ```

2. When you submit a password reset request, the reset link will print in your console/terminal.

3. Copy and paste the link into your browser to reset the password.

---

## Troubleshooting

* **MySQL Client Missing Error:**

  If you get `ModuleNotFoundError: No module named 'mysqlclient'`, install it with:

  ```bash
  pip install mysqlclient
  ```

* **SMTP Authentication Error:**

  Make sure you use correct email and password. For Gmail, you might need to use App Passwords instead of your regular password.

* **Static files not loading:**

  During development, Django serves static files automatically. For production, you need to configure static files properly.

---

## Project Structure

```
AuthLog/
├── AuthLog/
│   ├── settings.py          # Project settings (DB, email, apps)
│   ├── urls.py              # Root URL routing
│   └── wsgi.py
├── grabsomore/              # Authentication app
│   ├── models.py
│   ├── views.py
│   ├── templates/
│   ├── urls.py
│   └── ...
├── eCommerce/               # eCommerce app
│   ├── models.py
│   ├── views.py
│   ├── templates/
│   └── urls.py
├── manage.py                # Django CLI utility
└── requirements.txt         # Python dependencies
```

---