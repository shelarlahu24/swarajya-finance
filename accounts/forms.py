from django import forms
from django.db import models
from decimal import Decimal
from datetime import timedelta
from .models import SavingAccount,AgentCommission, Transaction
from django.utils.translation import gettext_lazy as _

class SavingAccountForm(forms.ModelForm):
    class Meta:
        models=SavingAccount
        fields='__all__'

    def __init__(self, *args, **kwargs):
        super(SavingAccountForm, self).__init__(*args, **kwargs)
        # If account_number exists in form, set it as read-only and use the auto-generated value
        if 'account_number' in self.fields:
            self.fields['account_number'].widget.attrs['readonly'] = True  # Make field readonly
            if not self.instance.pk:  # Check if it's a new instance (add view)
                last_account = SavingAccount.objects.order_by("-id").first()
                next_number = 1 if not last_account else int(last_account.account_number) + 1
                self.initial['account_number'] = str(next_number).zfill(3)  # Auto-generate account number

class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ['account', 'amount', 'payment_mode']

    account = forms.ModelChoiceField(queryset=SavingAccount.objects.all(), label='Account', empty_label="Choose an account", widget=forms.Select(attrs={'class': 'form-control'}))
    amount = forms.DecimalField(max_digits=10, decimal_places=2, widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}))
    payment_mode = forms.ChoiceField(choices=[('cash', 'Cash'), ('online', 'Online')], widget=forms.Select(attrs={'class': 'form-control'}))


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