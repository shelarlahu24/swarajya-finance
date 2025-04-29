from django import forms
from django.db import models
from decimal import Decimal
from datetime import timedelta
from .models import SavingAccount, Transaction
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
