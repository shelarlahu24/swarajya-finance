from django.db import models
from django.core.exceptions import ValidationError
from django.conf import settings
from core.models import FinanceSettings
from datetime import date,timedelta
from django.utils.timezone import now
from decimal import Decimal,ROUND_DOWN,ROUND_HALF_UP

# Create your models here.
class SavingAccount(models.Model):
    agent=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.SET_NULL,null=True,related_name='assigned_saving_accounts')
    account_number=models.CharField(max_length=3,unique=True)
    full_name=models.CharField(max_length=100)
    phone=models.CharField(unique=True, max_length=10)
    alternative_phone=models.CharField(unique=True, max_length=10,null=True, blank=True)
    address=models.TextField()
    is_active=models.BooleanField(default=True)
    eligible_for_loan=models.BooleanField(default=False)
    total_savings=models.DecimalField(max_digits=10, decimal_places=2,default=0.00)
    last_withdrawal_date = models.DateField(null=True, blank=True)
    created_at = models.DateField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now_add=True)

    #Nominee details
    nominee_name=models.CharField(max_length=100)
    nominee_relation=models.CharField(max_length=50)

    def __str__(self):
        return f"Account #{self.account_number} - {self.full_name}"
    
    @property
    def days_active(self):
        if not self.is_active:
            return 0
        start_date=self.last_withdrawal_date or self.created_at or date.today()
        return (date.today() - start_date).days
    
    @property
    def is_eligible_for_loan(self):
        settings = FinanceSettings.get_settings()
        return self.is_active and self.days_active >= int(settings.loan_eligible_days)
    
    @property
    def apply_commission(self):
        settings = FinanceSettings.get_settings()
        return self.days_active < int(settings.minimum_active_days)

    @property
    def apply_interest(self):
        settings = FinanceSettings.get_settings()
        return self.days_active >= int(settings.minimum_active_days)
    
    @property
    def total_deposit(self):
        return self.account_transactions.filter(transaction_type='deposit').aggregate(
            total=models.Sum('amount')
        )['total'] or 0
    
    @property
    def total_withdrawal(self):
        return self.account_transactions.filter(transaction_type='withdrawal').aggregate(
            total=models.Sum('amount')
        )['total'] or 0
    
    @property
    def total_saving(self):
        return Decimal(self.total_savings)

    
    @property
    def balance(self):
        settings = FinanceSettings.get_settings()
        base = self.total_saving

        if not self.is_active:
            return base

        interest = Decimal('0.00')
        commission = Decimal('0.00')

        if self.apply_interest:
            interest_rate = Decimal(str(settings.interest_earn)) / Decimal('100')
            interest = base * interest_rate
        elif self.apply_commission:
            commission_rate = Decimal(str(settings.commission_deducted)) / Decimal('100')
            commission = base * commission_rate

        return base + interest - commission

    def save(self, *args, **kwargs):
        # Auto-generate account number
        # if not self.account_number:
        #     last_account=SavingAccount.objects.order_by("-id").first()
        #     next_number=1 if not last_account else int(last_account.account_number)+1
        #     self.account_number=str(next_number).zfill(3)

        # Set loan eligibility
        self.eligible_for_loan = self.is_eligible_for_loan

        return super().save(*args,**kwargs)
    
class Transaction(models.Model):
    TRANSACTION_TYPES=(
        ('deposit','Deposit'),
        ('withdrawal','Withdrawal'),
        ('commission', 'Commission'),
        ('interest', 'Interest'),
    )

    PAYMENT_MODE=(
        ('online','Online'),
        ('cash','Cash'),
    )

    saving_account=models.ForeignKey(SavingAccount,on_delete=models.CASCADE,related_name="account_transactions")
    transaction_type=models.CharField(max_length=50,choices=TRANSACTION_TYPES)
    amount=models.DecimalField(max_digits=10, decimal_places=2)
    date=models.DateField(auto_now_add=True)
    payment_mode=models.CharField(max_length=10,choices=PAYMENT_MODE,default='cash')
    agent=models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,blank=True,null=True,related_name="user_transactions")

    def __str__(self):
        return f"{self.transaction_type.title()} of ₹{self.amount} on {self.date} (Account{self.saving_account.account_number})"
    
    def clean(self):
        if self.transaction_type == 'withdrawal':
            withdrawal_amount = Decimal(self.amount).quantize(Decimal('0.01'), rounding=ROUND_DOWN)
            total_savings = Decimal(self.saving_account.total_savings).quantize(Decimal('0.01'), rounding=ROUND_DOWN)

            if withdrawal_amount > total_savings:
                raise ValidationError(
                    f"❌ Insufficient balance. Available savings: ₹{total_savings:.2f}, you tried to withdraw: ₹{withdrawal_amount:.2f}."
                )

        super().clean()
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super(Transaction, self).save(*args, **kwargs)

        account = self.saving_account
        settings = FinanceSettings.get_settings()

        if self.transaction_type == 'withdrawal':
            account.last_withdrawal_date = self.date or now()

            # Use full amount as total deduction (user enters ₹100)
            total_deduction = Decimal(self.amount).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

            if account.apply_commission:
                # Exact 3% commission of total deduction
                commission_percent = Decimal(settings.commission_deducted)  # e.g. 3
                commission_amount = (total_deduction * commission_percent / Decimal('100')).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                actual_withdrawal = (total_deduction - commission_amount).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

                # Update this transaction to actual withdrawal amount
                self.amount = actual_withdrawal
                self.remarks = f"Withdrawal after {commission_percent}% commission"
                super(Transaction, self).save(update_fields=["amount", "remarks"])  # safe second call

                # Create commission transaction
                Transaction.objects.create(
                    saving_account=account,
                    transaction_type='commission',
                    amount=commission_amount,
                    date=self.date,
                    remarks=f"{commission_percent}% commission on withdrawal",
                    agent=self.agent  # Include agent if available
                )

                # Deduct full amount from total savings
                account.total_savings -= total_deduction

            elif account.apply_interest:
                interest_percent = Decimal(settings.interest_earn)  # e.g. 4
                interest_amount = (total_deduction * interest_percent / Decimal('100')).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                actual_withdrawal = total_deduction

                self.amount = actual_withdrawal
                self.remarks = f"Withdrawal + {interest_percent}% interest"
                super(Transaction, self).save(update_fields=["amount", "remarks"])  # safe second call


                Transaction.objects.create(
                    saving_account=account,
                    transaction_type='interest',
                    amount=interest_amount,
                    date=self.date,
                    remarks=f"{interest_percent}% interest on withdrawal",
                    agent=self.agent
                )

                account.total_savings -= (total_deduction + interest_amount)

            else:
                # No commission/interest
                account.total_savings -= total_deduction

            # Prevent negative savings
            account.total_savings = max(account.total_savings, Decimal('0.00'))

            # Deactivate account if empty
            if account.total_savings <= 0:
                account.is_active = False

        elif self.transaction_type == 'deposit':
            account.is_active = True
            if not account.last_withdrawal_date:
                account.last_withdrawal_date = account.created_at or now()
            account.total_savings += Decimal(self.amount)

        account.save()

class AgentCommission(models.Model):
    agent = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='commissions')
    month = models.DateField(help_text="Month this commission is for (use 1st of the month)")
    total_collection = models.DecimalField(max_digits=10, decimal_places=2)
    commission = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    def calculate_commission(self):
        settings = FinanceSettings.get_settings()
        commission_rate = Decimal(str(settings.agent_commission_rate)) / Decimal('100')

        total_collection = self.calculate_total_collection()
        self.total_collection = total_collection
        self.commission = total_collection * commission_rate

    def calculate_total_collection(self):
        first_day_of_month = self.month.replace(day=1)
        last_day_of_month = (first_day_of_month.replace(month=first_day_of_month.month + 1) - timedelta(days=1))

        total_collection = Transaction.objects.filter(
            agent=self.agent,
            transaction_type='deposit',
            date__range=(first_day_of_month, last_day_of_month)
        ).aggregate(total=models.Sum('amount'))['total'] or Decimal('0.00')

        return total_collection

    def save(self, *args, **kwargs):
        # Calculate commission first
        self.calculate_commission()

        # Check if a record already exists for this agent and month
        existing = AgentCommission.objects.filter(agent=self.agent, month=self.month).first()

        if existing and not self.pk:
            # If adding a new one but record exists — update the existing one
            existing.total_collection = self.total_collection
            existing.commission = self.commission
            existing.save(update_fields=['total_collection', 'commission'])
        else:
            # Normal save (new or updating this current one)
            super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.agent} - {self.month.strftime('%B %Y')}"