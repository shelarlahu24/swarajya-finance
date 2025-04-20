from django.contrib import admin
from .models import Customer
from django.http import HttpResponse
from openpyxl import Workbook
# Register your models here.

def export_customers_excel(modeladmin, request, queryset):
    wb = Workbook()
    ws = wb.active
    ws.title = "Customers"

    # Headers
    ws.append(['ID', 'Fullname', 'Phone','Email', 'Address','Aadhar Number','Pan Number','Agent','Created At'])

    # Data
    for customer in queryset.order_by('id'):
        ws.append([
            customer.id,
            customer.full_name,
            customer.phone,
            customer.email,
            customer.address,
            customer.aadhar_number,
            customer.pan_number,
            customer.agent.get_full_name(),
            customer.created_at.strftime('%Y-%m-%d')
        ])

    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename=customers.xlsx'
    wb.save(response)
    return response
export_customers_excel.short_description = "Export Selected Customers to Excel"


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'phone', 'aadhar_number', 'pan_number', 'agent', 'created_at')
    search_fields = ('full_name', 'phone', 'aadhar_number', 'pan_number')
    list_filter = ('created_at', 'agent')
    autocomplete_fields = ['agent']
    actions = [export_customers_excel]
