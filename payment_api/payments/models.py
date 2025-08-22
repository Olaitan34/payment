from django.db import models
from phonenumber_field.modelfields import PhoneNumberField

class Payment(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        COMPLETED = 'completed', 'Completed'
        FAILED = 'failed', 'Failed'

    id = models.AutoField(primary_key=True)

    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    phone_number = PhoneNumberField(unique=True, region="NG", max_length=20)
    email = models.EmailField(max_length=200)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    state = models.CharField(max_length=50)
    country = models.CharField(max_length=50)

    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.PENDING,
    )

    created_at = models.DateTimeField(auto_now_add=True)  # good for tracking
    updated_at = models.DateTimeField(auto_now=True)      # auto update

    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.amount} ({self.status})"