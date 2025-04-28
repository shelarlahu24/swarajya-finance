from django.contrib import admin
from .models import FinanceSettings
from django.utils import timezone
from django.db.models import Sum
from accounts.models import Transaction
# Register your models here.
@admin.register(FinanceSettings)
class FinanceSettingsAdmin(admin.ModelAdmin):

    def has_add_permission(self, request):
        # Prevent adding more than one instance
        return not FinanceSettings.objects.exists()
    
class CustomAdminSite(admin.AdminSite):
    site_header = "Swarajya Finance Admin"

    def index(self, request, extra_context=None):
        today = timezone.now().date()
        current_month = today.month
        current_year = today.year

        todays_collection = Transaction.objects.filter(
            date=today,
            transaction_type='deposit'
        ).aggregate(total=Sum('amount'))['total'] or 0

        monthly_collection = Transaction.objects.filter(
            date__year=current_year,
            date__month=current_month,
            transaction_type='deposit'
        ).aggregate(total=Sum('amount'))['total'] or 0

        if extra_context is None:
            extra_context = {}

        extra_context['total_customers'] = 100
        extra_context['todays_collection'] = todays_collection
        extra_context['monthly_collection'] = monthly_collection
        print(extra_context)

        return super().index(request, extra_context=extra_context)
