from rest_framework import serializers
from .models import Payment

class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = [
            'id',
            'first_name',
            'last_name',
            'email',
            'amount',
            'country',
            'status',
        ]      
        read_only_fields = ['status']  # prevent clients from changing status directly

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Amount must be greater than zero.")
        return value