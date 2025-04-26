# 🏠 Django Property Management REST API

This is a RESTful API for a Property Management System built with Django and Django REST Framework. The system supports functionalities for both property owners and tenants including property listings, applications, payments, notifications, reviews, and dashboards.

## 🚀 Features

- User Registration & Login (Token-based Authentication)
- Property CRUD with multiple image uploads
- Application system for tenants
- Approval & Rejection of applications by owners
- In-app notifications for application status
- Tenant and Owner dashboards
- Payment system for tenants
- Property review system
- Filtering and searching properties

## 📦 Tech Stack

- Python 3
- Django
- Django REST Framework
- SQLite/MySQL/PostgreSQL (you can configure)
- JWT or Token Authentication
- Git & GitHub

## 📁 API Endpoints

| Endpoint | Method | Description |
|---------|--------|-------------|
| `/register/` | POST | User Registration |
| `/login/` | POST | User Login |
| `/create-property/` | POST | Add a Property |
| `/my-properties/` | GET | Owner's Properties |
| `/properties/available/` | GET | List Available Properties |
| `/property/<id>/` | GET | Get Property Details |
| `/property/<id>/edit/` | PUT | Update Property |
| `/property/<id>/delete/` | DELETE | Delete Property |
| `/apply/<property_id>/` | POST | Tenant Apply to Property |
| `/applications/` | GET | Owner View Applications |
| `/tenant/applications/` | GET | Tenant View Applications |
| `/application/<id>/cancel/` | DELETE | Cancel Application |
| `/apply/change-status/<id>/` | PATCH | Change Application Status |
| `/notifications/` | GET | List Notifications |
| `/notifications/<id>/read/` | PATCH | Mark Notification as Read |
| `/owner/dashboard/` | GET | Owner Dashboard Stats |
| `/tenant/dashboard/` | GET | Tenant Dashboard Stats |
| `/payments/` | GET | List Payments |
| `/payments/create/<property_id>/` | POST | Create Payment |
| `/payments/update/<payment_id>/` | PATCH | Update Payment Status |
| `/properties/<id>/reviews/` | GET | List Reviews |
| `/properties/<id>/reviews/submit/` | POST | Submit Review |
| `/reviews/<review_id>/update/` | PATCH | Update Review |
| `/properties/applied/` | GET | Properties Applied by Tenant |
| `/properties/with-applicants/` | GET | Properties with Applicants |

## 🛠️ Setup Instructions

```bash
git clone https://github.com/Vijay-FS-10/B-Works.git
cd B-Works
python -m venv venv
source venv/bin/activate    # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python manage.py makemigrations
python manage.py migrate
python manage.py runserver
