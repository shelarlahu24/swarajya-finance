from .models import SavingAccount,Transaction, AgentProxy
from django.utils.translation import gettext_lazy as _
from django.shortcuts import render,get_object_or_404
from rangefilter.filters import DateRangeFilter
from decimal import Decimal,ROUND_HALF_UP
from django.utils.html import format_html
from core.models import FinanceSettings
from .forms import SavingAccountForm
from django.urls import path,reverse
from django.http import HttpResponse
from datetime import date,datetime
from django.contrib import admin
from django.db.models import Sum
from openpyxl import Workbook
# Register your models here.


# start filter class
class MonthFilter(admin.SimpleListFilter):
    title = 'Month'
    parameter_name = 'month'

    def lookups(self, request, model_admin):
        return [(i, datetime(2000, i, 1).strftime('%B')) for i in range(1, 13)]

    def queryset(self, request, queryset):
        return queryset


class YearFilter(admin.SimpleListFilter):
    title = 'Year'
    parameter_name = 'year'

    def lookups(self, request, model_admin):
        years = Transaction.objects.dates('date', 'year')
        return [(year.year, year.year) for year in years]

    def queryset(self, request, queryset):
        return queryset

    
# end filter class

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
            'fields': ('account_number','agent', 'full_name','phone','alternative_phone','address'),
        }),
        ('Account Overview', {
            'fields': ('is_active', 'eligible_for_loan_status','days_active_display','total_savings','commission_display','interest_display','balance_display'),
        }),
        ('Nominee Info', {
            'fields': ('nominee_name', 'nominee_relation'),
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

    list_display = ('saving_account', 'transaction_type', 'amount', 'date','agent','payment_mode')
    list_filter = (
        'transaction_type',
        'agent',
        'saving_account__account_number',
        'date',
    )
    # search_fields = ('saving_account__account_number',)
    actions = [export_transactions_excel]

    fieldsets = (
        (None,{
            'fields': ('saving_account', 'transaction_type', 'amount', 'payment_mode'),
        }),
    )

    def formfield_for_choice_field(self, db_field, request, **kwargs):
        if db_field.name=='transaction_type':
            kwargs['choices']=[
                ('deposit','Deposit'),
                ('withdrawal','Withdrawal')
            ]
        return super().formfield_for_choice_field(db_field, request, **kwargs)
    
    # Auto-assign agent
    def save_model(self, request, obj, form, change):
        if not obj.agent:
            obj.agent=request.user
        return super().save_model(request, obj, form, change)
    

@admin.register(AgentProxy)
class AgentCommissionAdmin(admin.ModelAdmin):
    list_display = ('name', 'monthly_collection_display', 'commission_display', 'view_details')
    list_filter = (MonthFilter, YearFilter)

    def get_queryset(self, request):
        self.request = request  # Store request for use in other methods
        return super().get_queryset(request).filter(role='agent')

    def name(self, obj):
        return obj.get_full_name() or obj.username

    def get_selected_month_year(self):
        today = datetime.today()
        month = int(self.request.GET.get('month', today.month))
        year = int(self.request.GET.get('year', today.year))
        return month, year

    def monthly_collection(self, obj):
        month, year = self.get_selected_month_year()
        # savings = SavingAccount.objects.filter(agent=obj)
        txns = Transaction.objects.filter(
            # saving_account__in=savings,
            agent=obj,  # Correct: transactions collected by the agent
            transaction_type='deposit',  # Optional: only include deposits if needed
            date__month=month,
            date__year=year
        )
        return txns.aggregate(total=Sum('amount'))['total'] or 0

    def commission(self, obj):
        total = self.monthly_collection(obj)
        settings=FinanceSettings.get_settings()
        commission_rate=Decimal(settings.commission_deducted) / Decimal(100)
        return (Decimal(total) * commission_rate).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    def monthly_collection_display(self, obj):
        return self.monthly_collection(obj)
    monthly_collection_display.short_description = 'Monthly Collection'

    def commission_display(self, obj):
        return self.commission(obj)
    commission_display.short_description = 'Commission'

    def view_details(self, obj):
        month, year = self.get_selected_month_year()
        url = reverse('admin:agent-customer-details', args=[obj.pk])
        full_url = f"{url}?month={month}&year={year}"
        return format_html('<a class="button" href="{}">View Details</a>', full_url)
    view_details.short_description = 'Details'

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('<int:agent_id>/customer-details/', self.admin_site.admin_view(self.customer_details_view), name='agent-customer-details'),
        ]
        return custom_urls + urls

    def customer_details_view(self, request, agent_id):
        agent = get_object_or_404(AgentProxy, pk=agent_id)
        today = datetime.today()
        month = int(request.GET.get('month', today.month))
        year = int(request.GET.get('year', today.year))

        customers = SavingAccount.objects.filter(agent=agent)
        customer_data = []
        settings=FinanceSettings.get_settings()
        commission_rate=Decimal(settings.commission_deducted) / Decimal(100)

        for customer in customers:
            total = Transaction.objects.filter(
                agent=agent,  # Correct: transactions collected by the agent
                transaction_type='deposit',
                date__month=month,
                date__year=year
            ).aggregate(total=Sum('amount'))['total'] or 0

            
            commission_value = (Decimal(total) * commission_rate).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    
            customer_data.append({
                'name': customer.full_name or customer.username,
                'total': total,
                'commission_value':commission_value
            })

        month_year_label = datetime(year, month, 1).strftime('%B %Y')

        context = {
             **self.admin_site.each_context(request),
            'agent': agent,
            'month_year': month_year_label,
            'customer_data': customer_data,
            'opts': self.model._meta,
            'back_url': reverse('admin:accounts_agentproxy_changelist')
        }

        return render(request, 'admin/agent_customer_details.html', context)