from django.urls import path
from . import views

app_name = "waste_management"

urlpatterns = [
    # Authentication endpoints
    path('auth/register/', views.UserRegistrationView.as_view(), name='register'),
    path('auth/login/', views.user_login, name='login'),
    path('auth/profile/', views.UserProfileView.as_view(), name='profile'),
    
    # Waste pickup endpoints
    path('pickups/', views.WastePickupListCreateView.as_view(), name='pickups-list'),
    path('pickups/<uuid:pk>/', views.WastePickupDetailView.as_view(), name='pickups-detail'),
    path('pickups/<uuid:pickup_id>/assign/', views.assign_pickup, name='assign-pickup'),
    
    # Referral endpoints
    path('referrals/', views.ReferralListView.as_view(), name='referrals-list'),
    
    # Points and transactions
    path('transactions/', views.PointsTransactionListView.as_view(), name='transactions-list'),
    path('withdrawals/', views.CashWithdrawalListCreateView.as_view(), name='withdrawals-list'),
    
    # Dashboard
    path('dashboard/', views.dashboard_stats, name='dashboard'),
]