from django import forms
from django.db import models
from decimal import Decimal
from datetime import timedelta
from .models import AgentCommission, Transaction
from django.utils.translation import gettext_lazy as _

class AgentCommissionForm(forms.ModelForm):
    class Meta:
        model = AgentCommission
        fields = ['agent', 'month']  # Only need to select Agent and Month
    
    # Method to dynamically calculate commission when agent and month are selected
    def clean(self):
        cleaned_data = super().clean()
        agent = cleaned_data.get('agent')
        month = cleaned_data.get('month')

        # If agent and month are provided, calculate total collection and commission
        if agent and month:
            first_day_of_month = month.replace(day=1)
            last_day_of_month = (first_day_of_month.replace(month=month.month % 12 + 1) - timedelta(days=1))

            total_collection = Transaction.objects.filter(
                agent=agent,
                transaction_type='deposit',
                date__range=(first_day_of_month, last_day_of_month)
            ).aggregate(total=models.Sum('amount'))['total'] or Decimal('0.00')

            commission = total_collection * Decimal('0.03')
            cleaned_data['total_collection'] = total_collection
            cleaned_data['commission'] = commission

        return cleaned_data