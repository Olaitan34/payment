from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Referral, WastePickup, PointsTransaction, CashWithdrawal


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ['username', 'email', 'user_type', 'points_balance', 'is_active']
    list_filter = ['user_type', 'is_active', 'date_joined']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    
    fieldsets = UserAdmin.fieldsets + (
        ('Additional Info', {
            'fields': ('user_type', 'phone_number', 'address', 'points_balance', 'referred_by')
        }),
    )
    
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Additional Info', {
            'fields': ('user_type', 'phone_number', 'address')
        }),
    )


@admin.register(Referral)
class ReferralAdmin(admin.ModelAdmin):
    list_display = ['referrer', 'referred_user', 'points_earned', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['referrer__username', 'referred_user__username']
    readonly_fields = ['created_at']


@admin.register(WastePickup)
class WastePickupAdmin(admin.ModelAdmin):
    list_display = ['disposer', 'collector', 'waste_type', 'status', 'scheduled_date', 'points_earned']
    list_filter = ['waste_type', 'status', 'scheduled_date']
    search_fields = ['disposer__username', 'collector__username', 'pickup_address']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'scheduled_date'


@admin.register(PointsTransaction)
class PointsTransactionAdmin(admin.ModelAdmin):
    list_display = ['user', 'transaction_type', 'points', 'cash_value', 'created_at']
    list_filter = ['transaction_type', 'created_at']
    search_fields = ['user__username', 'description']
    readonly_fields = ['created_at']


@admin.register(CashWithdrawal)
class CashWithdrawalAdmin(admin.ModelAdmin):
    list_display = ['user', 'points_redeemed', 'cash_amount', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['user__username', 'payment_reference']
    readonly_fields = ['created_at']
    actions = ['mark_as_processing', 'mark_as_completed']
    
    def mark_as_processing(self, request, queryset):
        queryset.update(status=CashWithdrawal.Status.PROCESSING)
    mark_as_processing.short_description = "Mark selected withdrawals as processing"
    
    def mark_as_completed(self, request, queryset):
        from django.utils import timezone
        queryset.update(
            status=CashWithdrawal.Status.COMPLETED,
            processed_at=timezone.now()
        )
    mark_as_completed.short_description = "Mark selected withdrawals as completed"
