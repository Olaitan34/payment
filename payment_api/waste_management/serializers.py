from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from .models import CustomUser, Referral, WastePickup, PointsTransaction, CashWithdrawal
from decimal import Decimal


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for user registration"""
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)
    referral_code = serializers.CharField(write_only=True, required=False, allow_blank=True)
    
    class Meta:
        model = CustomUser
        fields = [
            'username', 'email', 'first_name', 'last_name', 
            'password', 'password_confirm', 'user_type', 
            'phone_number', 'address', 'referral_code'
        ]
        extra_kwargs = {
            'email': {'required': True},
            'first_name': {'required': True},
            'last_name': {'required': True},
        }
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Passwords don't match")
        return attrs
    
    def validate_referral_code(self, value):
        if value:
            try:
                referrer = CustomUser.objects.get(username=value)
                return referrer
            except CustomUser.DoesNotExist:
                raise serializers.ValidationError("Invalid referral code")
        return None
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        referrer = validated_data.pop('referral_code', None)
        password = validated_data.pop('password')
        
        user = CustomUser.objects.create_user(
            password=password,
            **validated_data
        )
        
        # Handle referral
        if referrer:
            user.referred_by = referrer
            user.save()
            
            # Create referral record and award points
            Referral.objects.create(
                referrer=referrer,
                referred_user=user,
                status=Referral.Status.COMPLETED
            )
            
            # Award points to referrer
            referrer.points_balance += Decimal('100.00')
            referrer.save()
            
            # Create points transaction
            PointsTransaction.objects.create(
                user=referrer,
                transaction_type=PointsTransaction.TransactionType.REFERRAL,
                points=Decimal('100.00'),
                description=f"Referral bonus for {user.username}"
            )
        
        return user


class UserLoginSerializer(serializers.Serializer):
    """Serializer for user login"""
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)
    
    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')
        
        if username and password:
            user = authenticate(username=username, password=password)
            if not user:
                raise serializers.ValidationError("Invalid credentials")
            if not user.is_active:
                raise serializers.ValidationError("User account is disabled")
            attrs['user'] = user
        else:
            raise serializers.ValidationError("Must provide username and password")
        
        return attrs


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for user profile"""
    referral_count = serializers.SerializerMethodField()
    total_pickups = serializers.SerializerMethodField()
    
    class Meta:
        model = CustomUser
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'user_type', 'phone_number', 'address', 'points_balance',
            'referral_count', 'total_pickups', 'date_joined'
        ]
        read_only_fields = ['id', 'username', 'points_balance', 'date_joined']
    
    def get_referral_count(self, obj):
        return obj.made_referrals.filter(status=Referral.Status.COMPLETED).count()
    
    def get_total_pickups(self, obj):
        if obj.user_type == CustomUser.UserType.DISPOSER:
            return obj.pickup_requests.filter(status=WastePickup.Status.COMPLETED).count()
        elif obj.user_type == CustomUser.UserType.COLLECTOR:
            return obj.assigned_pickups.filter(status=WastePickup.Status.COMPLETED).count()
        return 0


class WastePickupSerializer(serializers.ModelSerializer):
    """Serializer for waste pickup scheduling"""
    disposer_name = serializers.CharField(source='disposer.get_full_name', read_only=True)
    collector_name = serializers.CharField(source='collector.get_full_name', read_only=True)
    
    class Meta:
        model = WastePickup
        fields = [
            'id', 'disposer', 'collector', 'waste_type', 'description',
            'pickup_address', 'scheduled_date', 'status', 'estimated_weight',
            'actual_weight', 'points_earned', 'disposer_name', 'collector_name',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'disposer', 'points_earned', 'created_at', 'updated_at']
    
    def create(self, validated_data):
        # Set the disposer to the current user if not provided
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['disposer'] = request.user
        return super().create(validated_data)


class WastePickupUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating waste pickup status (for collectors)"""
    
    class Meta:
        model = WastePickup
        fields = ['status', 'actual_weight']
    
    def update(self, instance, validated_data):
        if validated_data.get('status') == WastePickup.Status.COMPLETED:
            # Calculate points based on weight
            weight = validated_data.get('actual_weight', instance.estimated_weight)
            if weight:
                # 10 points per kg of waste
                points = Decimal(str(weight)) * Decimal('10.00')
                instance.points_earned = points
                
                # Award points to disposer
                instance.disposer.points_balance += points
                instance.disposer.save()
                
                # Create points transaction
                PointsTransaction.objects.create(
                    user=instance.disposer,
                    transaction_type=PointsTransaction.TransactionType.EARNED,
                    points=points,
                    description=f"Points for waste pickup #{instance.id}",
                    related_pickup=instance
                )
        
        return super().update(instance, validated_data)


class ReferralSerializer(serializers.ModelSerializer):
    """Serializer for referral records"""
    referrer_name = serializers.CharField(source='referrer.get_full_name', read_only=True)
    referred_user_name = serializers.CharField(source='referred_user.get_full_name', read_only=True)
    
    class Meta:
        model = Referral
        fields = [
            'id', 'referrer', 'referred_user', 'points_earned', 'status',
            'referrer_name', 'referred_user_name', 'created_at', 'completed_at'
        ]
        read_only_fields = ['id', 'points_earned', 'created_at', 'completed_at']


class PointsTransactionSerializer(serializers.ModelSerializer):
    """Serializer for points transactions"""
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    
    class Meta:
        model = PointsTransaction
        fields = [
            'id', 'user', 'transaction_type', 'points', 'cash_value',
            'description', 'user_name', 'created_at'
        ]
        read_only_fields = ['id', 'user', 'created_at']


class CashWithdrawalSerializer(serializers.ModelSerializer):
    """Serializer for cash withdrawal requests"""
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    
    class Meta:
        model = CashWithdrawal
        fields = [
            'id', 'user', 'points_redeemed', 'cash_amount', 'conversion_rate',
            'status', 'payment_reference', 'user_name', 'created_at', 'processed_at'
        ]
        read_only_fields = [
            'id', 'user', 'cash_amount', 'status', 'payment_reference', 
            'created_at', 'processed_at'
        ]
    
    def validate_points_redeemed(self, value):
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            if value > request.user.points_balance:
                raise serializers.ValidationError("Insufficient points balance")
        return value
    
    def create(self, validated_data):
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['user'] = request.user
            
            # Calculate cash amount based on conversion rate
            points = validated_data['points_redeemed']
            conversion_rate = validated_data.get('conversion_rate', Decimal('1.0000'))
            validated_data['cash_amount'] = points * conversion_rate
        
        return super().create(validated_data)