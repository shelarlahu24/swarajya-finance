from django.contrib import admin
from .models import SavingAccount,Transaction,AgentCommission
from core.models import FinanceSettings
from .forms import SavingAccountForm, AgentCommissionForm
from django import forms
from decimal import Decimal
from django.http import HttpResponse
from openpyxl import Workbook
# Register your models here.
@admin.register(SavingAccount)
class SavingAccountAdmin(admin.ModelAdmin):
    form = SavingAccountForm
    
    list_display = (
        'account_number',
        'full_name',
        'phone',
        'agent',
        'total_savings',
        'eligible_for_loan',
        'is_active',
        'created_at',
    )
    list_filter = ('eligible_for_loan', 'is_active', 'created_at','agent')
    search_fields = ('account_number', 'full_name','phone')
    readonly_fields = ('eligible_for_loan_status','total_savings',
                       'days_active_display','commission_display','interest_display','balance_display')

    fieldsets = (
        ('Account Info', {
            'fields': ('account_number','agent', 'full_name','phone','alternative_phone','address', 'is_active', 'eligible_for_loan_status'),
        }),
        ('Account Overview', {
            'fields': ('days_active_display','total_savings','commission_display','interest_display','balance_display'),
        }),
        ('Nominee Info', {
            'fields': ('nominee_name', 'nominee_relation', 'nominee_aadhar'),
        }),
    )

    def get_changeform_initial_data(self, request):
        initial = super().get_changeform_initial_data(request)
        last_account = SavingAccount.objects.order_by("-id").first()
        next_number = 1 if not last_account else int(last_account.account_number) + 1
        initial['account_number'] = str(next_number).zfill(3)
        return initial

    def days_active_display(self,obj):
        return obj.days_active
    days_active_display.short_description = "Active Days"

    def commission_display(self,obj):
        if obj.apply_commission:
            settings=FinanceSettings.get_settings()
            commission_rate=Decimal(settings.commission_deducted) / Decimal(100)
            commission=Decimal(obj.total_saving) * commission_rate
            return f"₹ {commission:.2f}"
        return "-"
    commission_display.short_description="Commission Deducted"

    def interest_display(self,obj):
        if obj.apply_interest:
            settings=FinanceSettings.get_settings()
            interest_rate=Decimal(settings.interest_earn) / Decimal(100)
            interest=Decimal(obj.total_saving) * interest_rate
            return f"₹ {interest:.2f}"
        return "-"
    interest_display.short_description="interest Earn"
    
    def balance_display(self,obj):
        return f"₹ {obj.balance:.2f}"
    balance_display.short_description="Balance"

    def eligible_for_loan_status(self, obj):
        return obj.is_eligible_for_loan
    eligible_for_loan_status.boolean = True
    eligible_for_loan_status.short_description = "Eligible for Loan"



def export_transactions_excel(modeladmin, request, queryset):
    wb = Workbook()
    ws = wb.active
    ws.title = "Transactions"

    # Headers
    ws.append(['ID', 'Customer', 'Date', 'Remark', 'Type','Amount'])

    # Data
    for tx in queryset:
        ws.append([
            tx.id,
            f"#{tx.saving_account}",
            tx.date.strftime('%Y-%m-%d'),
            tx.remarks,
            tx.transaction_type,
            float(tx.amount),
        ])

    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename=transactions.xlsx'
    wb.save(response)
    return response
export_transactions_excel.short_description = "Export Selected Transactions to Excel"

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):

    list_display = ('saving_account', 'transaction_type', 'amount', 'date','agent','remarks')
    list_filter = ('transaction_type', 'date','agent','saving_account__account_number')
    # search_fields = ('saving_account__account_number',)
    actions = [export_transactions_excel]

    fieldsets = (
        (None,{
            'fields': ('saving_account', 'transaction_type', 'amount', 'remarks'),
        }),
    )

    # Auto-assign agent
    def save_model(self, request, obj, form, change):
        if not obj.agent:
            obj.agent=request.user
        return super().save_model(request, obj, form, change)
    

#Commission Details
class CommissionForm(forms.Form):
    month = forms.DateField(
        label="Commission Month",
        help_text="Select any date within the target month",
        widget=forms.DateInput(attrs={'type': 'date'})  # 👈 This ensures a proper HTML5 date picker
    )

class AgentCommissionAdmin(admin.ModelAdmin):
    form = AgentCommissionForm

    list_display = ('agent', 'month', 'total_collection', 'commission')
    readonly_fields = ('total_collection', 'commission')  # Making fields readonly as they are auto-calculated

    def save_model(self, request, obj, form, change):
        # Auto-calculate commission before saving the object
        obj.calculate_commission()
        super().save_model(request, obj, form, change)

admin.site.register(AgentCommission, AgentCommissionAdmin)