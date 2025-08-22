import requests
from django.conf import settings
from django.shortcuts import render
from rest_framework import status, generics
from rest_framework.response import Response
from .serializers import PaymentSerializer
from .models import Payment


class PaymentInitiateView(generics.CreateAPIView):
    serializer_class = PaymentSerializer
    queryset = Payment.objects.all()
    
    def initialize_payment(self, payment):
        url = "https://api.paystack.co/transaction/initialize"
        headers = {
            "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
            "Content-Type": "application/json"
        }
        data = {
            "email": payment.email,
            "amount": int(payment.amount * 100),  # Convert to kobo
            "currency": "NGN",
            "callback_url": "https://hrapple-frontend.vercel.app/payment/success",
        }
        response = requests.post(url, headers=headers, json=data)
        res_data = response.json()

        if response.status_code == 200 and res_data.get("status") is True:
            payment.status = Payment.Status.PENDING
            payment.save()
        else:
            payment.status = Payment.Status.FAILED
            payment.save()
        return res_data
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payment = serializer.save()  # create Payment record
        payment_data = self.initialize_payment(payment)  # initialize Paystack
        return Response(payment_data, status=status.HTTP_201_CREATED)


class PaymentStatusView(generics.RetrieveAPIView):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
