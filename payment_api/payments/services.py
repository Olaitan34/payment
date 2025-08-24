import requests
import logging
from django.conf import settings
from typing import Dict, Any
from .models import Payment

logger = logging.getLogger(__name__)


class PaystackService:
    BASE_URL = "https://api.paystack.co"
    
    def __init__(self):
        self.secret_key = getattr(settings, 'PAYSTACK_SECRET_KEY', None)
        if not self.secret_key:
            raise ValueError("PAYSTACK_SECRET_KEY not configured in settings")
    
    def _get_headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.secret_key}",
            "Content-Type": "application/json"
        }
    
    def initialize_payment(self, payment: Payment) -> Dict[str, Any]:
        """Initialize payment with Paystack"""
        url = f"{self.BASE_URL}/transaction/initialize"
        
        data = {
            "email": payment.email,
            "amount": int(payment.amount * 100),  # Convert to kobo
            "currency": "NGN",
            "callback_url": getattr(
                settings, 
                "PAYSTACK_CALLBACK_URL", 
                "http://localhost:3000/payment/success"
            ),
            "metadata": {
                "payment_id": str(payment.id),
                "customer_name": f"{payment.first_name} {payment.last_name}"
            }
        }

        try:
            response = requests.post(
                url, 
                headers=self._get_headers(), 
                json=data, 
                timeout=30
            )
            response.raise_for_status()
            res_data = response.json()
            
            if res_data.get("status") is True:
                payment.reference = res_data["data"]["reference"]
                payment.status = Payment.Status.PENDING
                payment.save()
                logger.info(f"Payment initialized successfully: {payment.reference}")
            else:
                payment.status = Payment.Status.FAILED
                payment.save()
                logger.error(f"Payment initialization failed: {res_data}")
            
            return res_data
            
        except requests.RequestException as e:
            payment.status = Payment.Status.FAILED
            payment.save()
            error_msg = f"Error initializing payment: {str(e)}"
            logger.error(error_msg)
            return {"status": False, "message": error_msg}
        except Exception as e:
            payment.status = Payment.Status.FAILED
            payment.save()
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(error_msg)
            return {"status": False, "message": error_msg}

    def verify_payment(self, reference: str) -> Dict[str, Any]:
        """Verify payment status with Paystack"""
        url = f"{self.BASE_URL}/transaction/verify/{reference}"
        
        try:
            response = requests.get(
                url,
                headers=self._get_headers(),
                timeout=30
            )
            response.raise_for_status()
            res_data = response.json()
            
            logger.info(f"Payment verification response: {res_data}")
            return res_data
            
        except requests.RequestException as e:
            error_msg = f"Error verifying payment: {str(e)}"
            logger.error(error_msg)
            return {"status": False, "message": error_msg}
        except Exception as e:
            error_msg = f"Unexpected error during verification: {str(e)}"
            logger.error(error_msg)
            return {"status": False, "message": error_msg}