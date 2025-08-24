from rest_framework import status, generics
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from .serializers import PaymentCreateSerializer, PaymentDetailSerializer
from .models import Payment
from .services import PaystackService
import logging

logger = logging.getLogger(__name__)


class PaymentInitiateView(generics.CreateAPIView):
    """
    POST /api/v1/payments/
    Initiate a payment transaction
    """
    serializer_class = PaymentCreateSerializer
    queryset = Payment.objects.all()
    permission_classes = [AllowAny]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            payment = serializer.save()
            paystack_service = PaystackService()
            payment_data = paystack_service.initialize_payment(payment)
            
            if not payment_data.get("status"):
                return Response(
                    {
                        "payment": None,
                        "status": "error",
                        "message": payment_data.get("message", "Payment initialization failed")
                    }, 
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Return the Paystack response directly for payment 
            return Response(
                {
                    "status": payment_data.get("status"),
                    "message": payment_data.get("message"),
                    "data": {
                        "id": payment.id,  # <-- Add your DB id here
                        "authorization_url": payment_data["data"]["authorization_url"],
                        "access_code": payment_data["data"]["access_code"],
                        "reference": payment_data["data"]["reference"],
                    },
                },
                status=status.HTTP_201_CREATED,
            )

            # return Response(payment_data, status=status.HTTP_201_CREATED)
            
        except ValueError as e:
            logger.error(f"Configuration error: {str(e)}")
            return Response(
                {
                    "payment": None,
                    "status": "error",
                    "message": "Payment service not properly configured"
                }, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        except Exception as e:
            logger.error(f"Unexpected error in payment initiation: {str(e)}")
            return Response(
                {
                    "payment": None,
                    "status": "error",
                    "message": "An unexpected error occurred"
                }, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class PaymentListCreateView(generics.ListCreateAPIView):
    queryset = Payment.objects.all()
    serializer_class = PaymentCreateSerializer

class PaymentStatusView(generics.RetrieveAPIView):
    """
    GET /api/v1/payments/{id}/
    Retrieve the status of a specific payment transaction
    """
    queryset = Payment.objects.all()
    serializer_class = PaymentDetailSerializer
    permission_classes = [AllowAny]

    def retrieve(self, request, *args, **kwargs):
        payment = self.get_object()
        
        if not payment.reference:
            return Response(
                {
                    "payment": None,
                    "status": "error",
                    "message": "Payment reference not found"
                }, 
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            paystack_service = PaystackService()
            verification_data = paystack_service.verify_payment(payment.reference)
            
            if verification_data.get("status") is True:
                paystack_status = verification_data["data"]["status"]
                
                # Map Paystack status to our model choices
                if paystack_status == "success":
                    payment.status = Payment.Status.SUCCESS
                elif paystack_status == "failed":
                    payment.status = Payment.Status.FAILED
                else:
                    payment.status = Payment.Status.PENDING
                
                payment.save()
                
                # Use the detail serializer to format the response
                serializer = self.get_serializer(payment)
                payment_data = serializer.data
                
                # Format response according to specification
                return Response({
                    "payment": {
                        "id": payment_data["id"],
                        "customer_name": payment_data["customer_name"],
                        "customer_email": payment_data["customer_email"],
                        "amount": float(payment_data["amount"]),
                        "status": payment_data["status"]
                    },
                    "status": "success",
                    "message": "Payment details retrieved successfully."
                }, status=status.HTTP_200_OK)
            
            return Response(
                {
                    "payment": None,
                    "status": "error", 
                    "message": verification_data.get("message", "Unable to verify payment")
                }, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        except ValueError as e:
            logger.error(f"Configuration error: {str(e)}")
            return Response(
                {
                    "payment": None,
                    "status": "error",
                    "message": "Payment service not properly configured"
                }, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        except Exception as e:
            logger.error(f"Unexpected error in payment verification: {str(e)}")
            return Response(
                {
                    "payment": None,
                    "status": "error", 
                    "message": "An unexpected error occurred"
                }, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )