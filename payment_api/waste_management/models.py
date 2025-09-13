from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal
import uuid


class CustomUser(AbstractUser):
    """Custom user model with user types for waste management system"""
    class UserType(models.TextChoices):
        ADMIN = 'admin', 'Admin'
        COLLECTOR = 'collector', 'Collector' 
        DISPOSER = 'disposer', 'Disposer'
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_type = models.CharField(
        max_length=20,
        choices=UserType.choices,
        default=UserType.DISPOSER
    )
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    points_balance = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    referred_by = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='referrals'
    )
    
    def __str__(self):
        return f"{self.username} ({self.get_user_type_display()})"


class Referral(models.Model):
    """Track referrals and points earned"""
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        COMPLETED = 'completed', 'Completed'
        PAID = 'paid', 'Paid'
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    referrer = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='made_referrals'
    )
    referred_user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='referral_record'
    )
    points_earned = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('100.00')  # Default referral bonus
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.referrer.username} referred {self.referred_user.username}"


class WastePickup(models.Model):
    """Model for scheduling waste pickups"""
    class Status(models.TextChoices):
        SCHEDULED = 'scheduled', 'Scheduled'
        IN_PROGRESS = 'in_progress', 'In Progress'
        COMPLETED = 'completed', 'Completed'
        CANCELLED = 'cancelled', 'Cancelled'
    
    class WasteType(models.TextChoices):
        GENERAL = 'general', 'General Waste'
        RECYCLABLE = 'recyclable', 'Recyclable'
        ORGANIC = 'organic', 'Organic'
        HAZARDOUS = 'hazardous', 'Hazardous'
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    disposer = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='pickup_requests',
        limit_choices_to={'user_type': CustomUser.UserType.DISPOSER}
    )
    collector = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_pickups',
        limit_choices_to={'user_type': CustomUser.UserType.COLLECTOR}
    )
    waste_type = models.CharField(
        max_length=20,
        choices=WasteType.choices,
        default=WasteType.GENERAL
    )
    description = models.TextField(blank=True, null=True)
    pickup_address = models.TextField()
    scheduled_date = models.DateTimeField()
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.SCHEDULED
    )
    estimated_weight = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Estimated weight in kg"
    )
    actual_weight = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Actual weight in kg"
    )
    points_earned = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-scheduled_date']
    
    def __str__(self):
        return f"Pickup for {self.disposer.username} - {self.get_status_display()}"


class PointsTransaction(models.Model):
    """Track points transactions and cash conversions"""
    class TransactionType(models.TextChoices):
        EARNED = 'earned', 'Points Earned'
        REDEEMED = 'redeemed', 'Points Redeemed'
        REFERRAL = 'referral', 'Referral Bonus'
        BONUS = 'bonus', 'Bonus Points'
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='points_transactions'
    )
    transaction_type = models.CharField(
        max_length=20,
        choices=TransactionType.choices
    )
    points = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    cash_value = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Cash equivalent in NGN"
    )
    description = models.TextField(blank=True, null=True)
    related_pickup = models.ForeignKey(
        WastePickup,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='points_transactions'
    )
    related_referral = models.ForeignKey(
        Referral,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='points_transactions'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.get_transaction_type_display()}: {self.points} points"


class CashWithdrawal(models.Model):
    """Track cash withdrawals from points"""
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        PROCESSING = 'processing', 'Processing'
        COMPLETED = 'completed', 'Completed'
        FAILED = 'failed', 'Failed'
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='withdrawals'
    )
    points_redeemed = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    cash_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    conversion_rate = models.DecimalField(
        max_digits=6,
        decimal_places=4,
        default=Decimal('1.0000'),
        help_text="Points to NGN conversion rate"
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )
    payment_reference = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Reference from payment gateway"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.cash_amount} NGN withdrawal"
