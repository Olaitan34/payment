from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.authtoken.models import Token
from django.contrib.auth import login
from django.db.models import Q
from django.utils import timezone
from .models import CustomUser, Referral, WastePickup, PointsTransaction, CashWithdrawal
from .serializers import (
    UserRegistrationSerializer, UserLoginSerializer, UserProfileSerializer,
    WastePickupSerializer, WastePickupUpdateSerializer, ReferralSerializer,
    PointsTransactionSerializer, CashWithdrawalSerializer
)
import logging

logger = logging.getLogger(__name__)


class UserRegistrationView(generics.CreateAPIView):
    """User registration endpoint"""
    queryset = CustomUser.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Create token for the user
        token, created = Token.objects.get_or_create(user=user)
        
        return Response({
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'user_type': user.user_type,
                'points_balance': user.points_balance
            },
            'token': token.key,
            'message': 'User registered successfully'
        }, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([AllowAny])
def user_login(request):
    """User login endpoint"""
    serializer = UserLoginSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.validated_data['user']
        login(request, user)
        
        # Get or create token
        token, created = Token.objects.get_or_create(user=user)
        
        return Response({
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'user_type': user.user_type,
                'points_balance': user.points_balance
            },
            'token': token.key,
            'message': 'Login successful'
        }, status=status.HTTP_200_OK)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserProfileView(generics.RetrieveUpdateAPIView):
    """User profile endpoint"""
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]
    
    def get_object(self):
        return self.request.user


class WastePickupListCreateView(generics.ListCreateAPIView):
    """List and create waste pickups"""
    serializer_class = WastePickupSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.user_type == CustomUser.UserType.DISPOSER:
            return WastePickup.objects.filter(disposer=user)
        elif user.user_type == CustomUser.UserType.COLLECTOR:
            return WastePickup.objects.filter(
                Q(collector=user) | Q(collector__isnull=True)
            ).exclude(status=WastePickup.Status.CANCELLED)
        elif user.user_type == CustomUser.UserType.ADMIN:
            return WastePickup.objects.all()
        return WastePickup.objects.none()
    
    def perform_create(self, serializer):
        serializer.save(disposer=self.request.user)


class WastePickupDetailView(generics.RetrieveUpdateAPIView):
    """Retrieve and update waste pickup"""
    serializer_class = WastePickupSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.user_type == CustomUser.UserType.DISPOSER:
            return WastePickup.objects.filter(disposer=user)
        elif user.user_type == CustomUser.UserType.COLLECTOR:
            return WastePickup.objects.filter(
                Q(collector=user) | Q(collector__isnull=True)
            )
        elif user.user_type == CustomUser.UserType.ADMIN:
            return WastePickup.objects.all()
        return WastePickup.objects.none()
    
    def get_serializer_class(self):
        if self.request.user.user_type == CustomUser.UserType.COLLECTOR:
            return WastePickupUpdateSerializer
        return WastePickupSerializer


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def assign_pickup(request, pickup_id):
    """Assign pickup to collector"""
    try:
        pickup = WastePickup.objects.get(
            id=pickup_id,
            status=WastePickup.Status.SCHEDULED,
            collector__isnull=True
        )
        
        if request.user.user_type != CustomUser.UserType.COLLECTOR:
            return Response(
                {'error': 'Only collectors can assign pickups to themselves'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        pickup.collector = request.user
        pickup.status = WastePickup.Status.IN_PROGRESS
        pickup.save()
        
        return Response({
            'message': 'Pickup assigned successfully',
            'pickup_id': pickup.id
        }, status=status.HTTP_200_OK)
        
    except WastePickup.DoesNotExist:
        return Response(
            {'error': 'Pickup not found or already assigned'},
            status=status.HTTP_404_NOT_FOUND
        )


class ReferralListView(generics.ListAPIView):
    """List user's referrals"""
    serializer_class = ReferralSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Referral.objects.filter(referrer=self.request.user)


class PointsTransactionListView(generics.ListAPIView):
    """List user's points transactions"""
    serializer_class = PointsTransactionSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return PointsTransaction.objects.filter(user=self.request.user)


class CashWithdrawalListCreateView(generics.ListCreateAPIView):
    """List and create cash withdrawal requests"""
    serializer_class = CashWithdrawalSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return CashWithdrawal.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        withdrawal = serializer.save()
        
        # Deduct points from user's balance
        user = self.request.user
        user.points_balance -= withdrawal.points_redeemed
        user.save()
        
        # Create redemption transaction
        PointsTransaction.objects.create(
            user=user,
            transaction_type=PointsTransaction.TransactionType.REDEEMED,
            points=withdrawal.points_redeemed,
            cash_value=withdrawal.cash_amount,
            description=f"Cash withdrawal request #{withdrawal.id}"
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_stats(request):
    """Get dashboard statistics for the user"""
    user = request.user
    stats = {
        'points_balance': str(user.points_balance),
        'referral_count': user.made_referrals.filter(
            status=Referral.Status.COMPLETED
        ).count(),
        'total_transactions': user.points_transactions.count(),
    }
    
    if user.user_type == CustomUser.UserType.DISPOSER:
        stats.update({
            'total_pickups': user.pickup_requests.count(),
            'completed_pickups': user.pickup_requests.filter(
                status=WastePickup.Status.COMPLETED
            ).count(),
            'scheduled_pickups': user.pickup_requests.filter(
                status=WastePickup.Status.SCHEDULED
            ).count(),
        })
    elif user.user_type == CustomUser.UserType.COLLECTOR:
        stats.update({
            'assigned_pickups': user.assigned_pickups.count(),
            'completed_pickups': user.assigned_pickups.filter(
                status=WastePickup.Status.COMPLETED
            ).count(),
            'available_pickups': WastePickup.objects.filter(
                collector__isnull=True,
                status=WastePickup.Status.SCHEDULED
            ).count(),
        })
    elif user.user_type == CustomUser.UserType.ADMIN:
        stats.update({
            'total_users': CustomUser.objects.count(),
            'total_pickups': WastePickup.objects.count(),
            'pending_withdrawals': CashWithdrawal.objects.filter(
                status=CashWithdrawal.Status.PENDING
            ).count(),
        })
    
    return Response(stats, status=status.HTTP_200_OK)
