import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from unittest.mock import patch, MagicMock
from decimal import Decimal
from payments.models import Payment
from payments.services import PaystackService


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def sample_payment_data():
    return {
        "customer_name": "John Doe",
        "customer_email": "john@example.com",
        "amount": "5000.00",
        "country": "NG"
    }


# Simple tests matching your original pattern
@pytest.mark.django_db
def test_initiate_payment_success():
    client = APIClient()
    url = reverse('payments:payments-create')

    data = {
        "customer_name": "John Doe",
        "customer_email": "john@example.com",
        "amount": "5000.00",
        "country": "NG"
    }

    # Mock Paystack API response
    with patch("payments.services.requests.post") as mock_post:
        mock_response = mock_post.return_value
        mock_response.json.return_value = {
            "status": True,
            "data": {
                "authorization_url": "https://checkout.paystack.com/test123",
                "reference": "ref_test123"
            }
        }
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None

        response = client.post(url, data, format="json")

    assert response.status_code == 201
    assert response.data["status"] is True
    assert "authorization_url" in response.data["data"]
    assert Payment.objects.count() == 1
    payment = Payment.objects.first()
    assert payment.email == "john@example.com"
    assert payment.amount == Decimal("5000.00")


@pytest.mark.django_db 
def test_payment_status_success():
    client = APIClient()
    payment = Payment.objects.create(
        first_name="Jane",
        last_name="Doe",
        email="jane@example.com",
        amount=Decimal("7000.00"),
        country="NG",
        status=Payment.Status.PENDING,
        reference="ref_test123"
    )

    url = reverse("payments:payments-detail", args=[payment.id])

    with patch("payments.services.requests.get") as mock_get:
        mock_response = mock_get.return_value
        mock_response.json.return_value = {
            "status": True,
            "data": {"status": "success"}
        }
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None

        response = client.get(url)

    assert response.status_code == 200
    payment.refresh_from_db()
    assert payment.status == Payment.Status.SUCCESS
    
    # Check the new response format
    assert response.data["status"] == "success"
    assert response.data["message"] == "Payment details retrieved successfully."
    assert response.data["payment"]["id"] == str(payment.id)
    assert response.data["payment"]["customer_name"] == "Jane Doe"
    assert response.data["payment"]["customer_email"] == "jane@example.com"
    assert response.data["payment"]["amount"] == 7000.0
    assert response.data["payment"]["status"] == Payment.Status.SUCCESS


@pytest.mark.django_db
def test_payment_status_no_reference():
    client = APIClient()
    payment = Payment.objects.create(
        first_name="Jane",
        last_name="Doe", 
        email="jane@example.com",
        amount=Decimal("7000.00"),
        country="NG",
        status=Payment.Status.PENDING,
        reference=""  # No reference
    )
    
    url = reverse("payments:payments-detail", args=[payment.id])
    response = client.get(url)
    
    assert response.status_code == 400
    assert response.data["status"] == "error"
    assert response.data["payment"] is None
    assert "reference not found" in response.data["message"]