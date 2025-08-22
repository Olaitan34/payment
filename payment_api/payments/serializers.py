from rest_framework import serializers
from .models import Payment


class PaymentCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating payments"""
    customer_name = serializers.CharField(max_length=200, write_only=True)
    customer_email = serializers.EmailField(write_only=True)
    
    class Meta:
        model = Payment
        fields = ['customer_name', 'customer_email', 'amount', 'country']
        extra_kwargs = {
            'country': {'default': 'NG'}
        }

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Amount must be greater than zero.")
        return value

    def validate_customer_email(self, value):
        if not value:
            raise serializers.ValidationError("Customer email is required.")
        return value.lower()

    def create(self, validated_data):
        # Split customer_name into first_name and last_name
        customer_name = validated_data.pop('customer_name')
        customer_email = validated_data.pop('customer_email')
        
        name_parts = customer_name.strip().split(' ', 1)
        first_name = name_parts[0]
        last_name = name_parts[1] if len(name_parts) > 1 else ''
        
        return Payment.objects.create(
            first_name=first_name,
            last_name=last_name,
            email=customer_email,
            **validated_data
        )


class PaymentDetailSerializer(serializers.ModelSerializer):
    """Serializer for payment details response"""
    customer_name = serializers.SerializerMethodField()
    customer_email = serializers.CharField(source='email')
    
    class Meta:
        model = Payment
        fields = [
            'id',
            'customer_name', 
            'customer_email',
            'amount',
            'status',
            'reference',
            'created_at',
            'updated_at'
        ]
    
    def get_customer_name(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip()
