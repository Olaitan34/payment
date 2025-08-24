
---

# 💳 Paystack Payment System (Django REST API) - (BY FATOKI OLAITAN)

A Django-based REST API integration with **Paystack** 🚀
This package provides endpoints to **initialize** and **verify** payments, making it easy to add payment processing to your project.

🌍 **Deployed on Render** → Try it out live:

* 🔹 [POST /api/v1/payments/](https://paymentssss.onrender.com/api/v1/payments/) → Initiate a new payment
* 🔹 [GET /api/v1/payments/{id}/](https://paymentssss.onrender.com/api/v1/payments/{id}) → Verify a payment by ID
* 🔹 [Admin Panel](https://paymentssss.onrender.com/admin) → Manage payments & users

🛠 **Superuser Credentials** (for testing only):

* 👤 Username: `Ola34`
* 🔑 Password: `12345678`

---

## ✨ Features

* 🔐 Secure Paystack API integration
* 🛠 Create & track payment records
* 💸 Initialize payments with callback support
* ✅ Verify payment status in real time
* 📡 REST API endpoints for frontend/mobile apps
* 🧪 Unit tests with mocked Paystack API responses

---

## 📂 Project Structure

```
payments/
│
├── models.py            # Database model for payments
├── serializers.py       # Input/output data validation & formatting
├── services.py          # Paystack API service layer
├── views.py             # REST API views
├── urls.py              # App-specific routes
├── test_payments.py     # Unit tests with Pytest
```

---

## ⚙️ Installation & Setup

### 1️⃣ Clone Repository

```bash
git clone https://github.com/yourusername/paystack-payment-system.git
cd paystack-payment-system
```

### 2️⃣ Install Dependencies

```bash
pip install django djangorestframework requests pytest
```

### 3️⃣ Add App to Django Project

In `settings.py`:

```python
INSTALLED_APPS = [
    ...
    "rest_framework",
    "payments",
]
```

### 4️⃣ Configure Paystack Keys

In `settings.py`:

```python
PAYSTACK_SECRET_KEY = "your_paystack_secret_key"
PAYSTACK_CALLBACK_URL = "http://localhost:3000/payment/success"
```

### 5️⃣ Run Migrations

```bash
python manage.py makemigrations payments
python manage.py migrate
```

---

## 🚀 API Usage

### 🔹 1. **Initiate Payment**

**Endpoint:**
`POST /api/v1/payments/`

👉 Use this to **start a new payment transaction**.
It talks to Paystack and generates an **authorization URL** where your customer can pay.

**Request Body:**

```json
{
  "customer_name": "John Doe",
  "customer_email": "john@example.com",
  "amount": "5000.00",
  "country": "NG"
}
```

**Response (✅ Success):**

```json
{
  "status": true,
  "data": {
    "authorization_url": "https://checkout.paystack.com/xyz123",
    "reference": "ref_xyz123"
  }
}
```

---

### 🔹 2. **Verify Payment**

**Endpoint:**
`GET /api/v1/payments/{id}/`

👉 Use this to **check the status** of a specific payment using its unique ID.
It confirms whether the payment is ✅ `success`, ❌ `failed`, ⏳ `pending`, or 📴 `abandoned`.

**Response (✅ Success):**

```json
{
  "payment": {
    "id": "uuid",
    "customer_name": "Jane Doe",
    "customer_email": "jane@example.com",
    "amount": 7000.0,
    "status": "success"
  },
  "status": "success",
  "message": "Payment details retrieved successfully."
}
```

**Response (❌ Failure):**

```json
{
  "payment": null,
  "status": "error",
  "message": "Unable to verify payment"
}
```

---

### 🔹 3. **Admin Panel**

**Endpoint:**
`/admin`

👉 Here you can manage:

* ✅ All payment transactions
* 👤 Users & authentication
* 🛠 Debug and monitor your app

Use the provided **superuser credentials** to log in.

---

## 🛠 File-by-File Explanation

| File                  | Description                                                                                              |
| --------------------- | -------------------------------------------------------------------------------------------------------- |
| **models.py**         | Defines the `Payment` model with status (`pending`, `success`, `failed`, `abandoned`)                    |
| **serializers.py**    | Handles request validation (`PaymentCreateSerializer`) & response formatting (`PaymentDetailSerializer`) |
| **services.py**       | Handles Paystack API calls: `initialize_payment` & `verify_payment`                                      |
| **views.py**          | API endpoints: initiate (`POST`) & verify (`GET`) payments                                               |
| **urls.py**           | Routes for API endpoints `/api/v1/payments/` & `/api/v1/payments/<id>/`                                  |
| **test\_payments.py** | Unit tests using pytest & mock Paystack responses                                                        |

---

## 🧪 Running Tests

```bash
pytest payments/test_payments.py
```

---

## 📌 Example Project URL Configuration

In your project’s `urls.py`:

```python
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('payments.urls')),  # -> /api/v1/payments/
]
```

---

## 📖 Notes

* 💡 Default currency = `NGN` (Nigerian Naira).
* 🔑 Ensure your Paystack secret key is correct.
* 🌍 Works in both local & production environments.
* 🎉 Live demo already deployed on Render (see links above!)

---
