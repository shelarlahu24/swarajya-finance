from django.db import models

# Create your models here.
class FinanceSettings(models.Model):
    minimum_active_days=models.CharField(max_length=3,default=90)
    loan_eligible_days=models.CharField(max_length=3,default=45)
    commission_deducted=models.FloatField(default=3.0,help_text="Commission (%) for < minimum_active_days")
    interest_earn=models.FloatField(default=4.0,help_text="Interest (%) for ≥ minimum_active_days")
    agent_commission_rate=models.FloatField(default=3.0,help_text="Agent get commission after 1 month")

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
