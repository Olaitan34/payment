from django.urls import path, include
from . import views

app_name = "payments"  
# API v1 URLs
urlpatterns = [
    path('v1/payments/', views.PaymentInitiateView.as_view(), name='payments-create'),
    path('v1/payments/', views.PaymentListCreateView.as_view(), name='payments-list'),
    path('v1/payments/<uuid:pk>/', views.PaymentStatusView.as_view(), name='payments-detail'),
]
