from django.db import models
from decimal import Decimal

# Create your models here.
class FinanceSettings(models.Model):
    minimum_active_days = models.PositiveIntegerField(default=90)  # changed to PositiveIntegerField
    loan_eligible_days = models.PositiveIntegerField(default=45)   # changed to PositiveIntegerField
    commission_deducted = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=Decimal('3.00'), 
        help_text="Commission (%) for < minimum_active_days"
    )
    interest_earn = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=Decimal('4.00'), 
        help_text="Interest (%) for ≥ minimum_active_days"
    )
    agent_commission_rate = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=Decimal('3.00'), 
        help_text="Agent get commission after 1 month"
    )

    class Meta:
        verbose_name="Finance Setting"
        verbose_name_plural="Finance Settings"

    def __str__(self):
        return "Finance Settings"
    
    def save(self, *args,**kwargs):
        self.pk=1
        super().save(*args,**kwargs)

    @classmethod
    def get_settings(cls):
        obj,created=cls.objects.get_or_create(pk=1)
        return obj
