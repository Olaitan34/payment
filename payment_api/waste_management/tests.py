from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework.authtoken.models import Token
from decimal import Decimal
from .models import CustomUser, Referral, WastePickup, PointsTransaction, CashWithdrawal

User = get_user_model()


class UserRegistrationTestCase(APITestCase):
    def test_user_registration_success(self):
        """Test successful user registration"""
        url = reverse('waste_management:register')
        data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'first_name': 'Test',
            'last_name': 'User',
            'password': 'testpass123',
            'password_confirm': 'testpass123',
            'user_type': 'disposer',
            'phone_number': '+2347000000000'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('token', response.data)
        self.assertEqual(response.data['user']['username'], 'testuser')
        self.assertEqual(response.data['user']['user_type'], 'disposer')
        
        # Check user was created in database
        user = User.objects.get(username='testuser')
        self.assertEqual(user.email, 'test@example.com')
        self.assertEqual(user.user_type, 'disposer')
    
    def test_user_registration_with_referral(self):
        """Test user registration with referral code"""
        # Create referrer
        referrer = User.objects.create_user(
            username='referrer',
            email='referrer@example.com',
            password='password123',
            user_type='disposer'
        )
        
        url = reverse('waste_management:register')
        data = {
            'username': 'newuser',
            'email': 'new@example.com',
            'first_name': 'New',
            'last_name': 'User',
            'password': 'testpass123',
            'password_confirm': 'testpass123',
            'user_type': 'disposer',
            'referral_code': 'referrer'  # Using username as referral code
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Check referral was created
        new_user = User.objects.get(username='newuser')
        self.assertEqual(new_user.referred_by, referrer)
        
        # Check referrer got points
        referrer.refresh_from_db()
        self.assertEqual(referrer.points_balance, Decimal('100.00'))
        
        # Check referral record exists
        referral = Referral.objects.get(referred_user=new_user)
        self.assertEqual(referral.referrer, referrer)
        self.assertEqual(referral.status, Referral.Status.COMPLETED)


class UserLoginTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            user_type='disposer'
        )
    
    def test_user_login_success(self):
        """Test successful user login"""
        url = reverse('waste_management:login')
        data = {
            'username': 'testuser',
            'password': 'testpass123'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.data)
        self.assertEqual(response.data['user']['username'], 'testuser')
    
    def test_user_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        url = reverse('waste_management:login')
        data = {
            'username': 'testuser',
            'password': 'wrongpassword'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class WastePickupTestCase(APITestCase):
    def setUp(self):
        self.disposer = User.objects.create_user(
            username='disposer',
            email='disposer@example.com',
            password='password123',
            user_type='disposer'
        )
        self.collector = User.objects.create_user(
            username='collector',
            email='collector@example.com',
            password='password123',
            user_type='collector'
        )
        self.disposer_token = Token.objects.create(user=self.disposer)
        self.collector_token = Token.objects.create(user=self.collector)
    
    def test_create_waste_pickup(self):
        """Test creating a waste pickup request"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.disposer_token.key}')
        
        url = reverse('waste_management:pickups-list')
        data = {
            'waste_type': 'recyclable',
            'description': 'Plastic bottles and cans',
            'pickup_address': '123 Test Street, Lagos',
            'scheduled_date': '2024-01-15T10:00:00Z',
            'estimated_weight': '5.50'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['waste_type'], 'recyclable')
        self.assertEqual(response.data['disposer'], self.disposer.id)
    
    def test_assign_pickup_to_collector(self):
        """Test collector assigning pickup to themselves"""
        pickup = WastePickup.objects.create(
            disposer=self.disposer,
            waste_type='general',
            pickup_address='Test Address',
            scheduled_date='2024-01-15T10:00:00Z',
            estimated_weight=Decimal('3.00')
        )
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.collector_token.key}')
        
        url = reverse('waste_management:assign-pickup', args=[pickup.id])
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        pickup.refresh_from_db()
        self.assertEqual(pickup.collector, self.collector)
        self.assertEqual(pickup.status, WastePickup.Status.IN_PROGRESS)
    
    def test_complete_pickup_awards_points(self):
        """Test that completing a pickup awards points to disposer"""
        pickup = WastePickup.objects.create(
            disposer=self.disposer,
            collector=self.collector,
            waste_type='general',
            pickup_address='Test Address',
            scheduled_date='2024-01-15T10:00:00Z',
            estimated_weight=Decimal('3.00'),
            status=WastePickup.Status.IN_PROGRESS
        )
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.collector_token.key}')
        
        url = reverse('waste_management:pickups-detail', args=[pickup.id])
        data = {
            'status': 'completed',
            'actual_weight': '4.50'
        }
        
        response = self.client.patch(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check points were awarded
        self.disposer.refresh_from_db()
        expected_points = Decimal('4.50') * Decimal('10.00')  # 10 points per kg
        self.assertEqual(self.disposer.points_balance, expected_points)
        
        # Check transaction was created
        transaction = PointsTransaction.objects.get(
            user=self.disposer,
            transaction_type=PointsTransaction.TransactionType.EARNED
        )
        self.assertEqual(transaction.points, expected_points)


class CashWithdrawalTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password123',
            user_type='disposer',
            points_balance=Decimal('500.00')
        )
        self.token = Token.objects.create(user=self.user)
    
    def test_create_cash_withdrawal(self):
        """Test creating a cash withdrawal request"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        
        url = reverse('waste_management:withdrawals-list')
        data = {
            'points_redeemed': '100.00',
            'conversion_rate': '1.0000'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['points_redeemed'], '100.00')
        self.assertEqual(response.data['cash_amount'], '100.00')
        
        # Check points were deducted
        self.user.refresh_from_db()
        self.assertEqual(self.user.points_balance, Decimal('400.00'))
    
    def test_withdraw_insufficient_points(self):
        """Test withdrawal with insufficient points"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        
        url = reverse('waste_management:withdrawals-list')
        data = {
            'points_redeemed': '600.00',  # More than available
            'conversion_rate': '1.0000'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class DashboardStatsTestCase(APITestCase):
    def setUp(self):
        self.disposer = User.objects.create_user(
            username='disposer',
            email='disposer@example.com',
            password='password123',
            user_type='disposer',
            points_balance=Decimal('200.00')
        )
        self.token = Token.objects.create(user=self.disposer)
        
        # Create some test data
        WastePickup.objects.create(
            disposer=self.disposer,
            waste_type='general',
            pickup_address='Test Address',
            scheduled_date='2024-01-15T10:00:00Z',
            status=WastePickup.Status.COMPLETED
        )
    
    def test_dashboard_stats(self):
        """Test dashboard statistics endpoint"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        
        url = reverse('waste_management:dashboard')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['points_balance'], '200.00')
        self.assertEqual(response.data['total_pickups'], 1)
        self.assertEqual(response.data['completed_pickups'], 1)
