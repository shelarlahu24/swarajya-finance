from django.shortcuts import render,redirect
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from customers.models import Customer
from django.contrib import messages
from django.db.models import Sum
from accounts.models import SavingAccount,Transaction
from datetime import date
from collections import defaultdict
from decimal import Decimal
import calendar

# Create your views here.
@login_required(login_url="login")
def dashboard_view(request):

    agent = request.user
    today = date.today()
    year=today.year
    month=today.month
    num_days = calendar.monthrange(year,month)[1]

    # Daily total deposit for each day of current month
    start_date=date(year,month,1)
    end_date=date(year,month,num_days)

    monthly_transaction=Transaction.objects.filter(
        agent=agent,
        transaction_type="deposit",
        date__range=(start_date,end_date)
    )

    # Build daily data dictionary
    daily_data=defaultdict(lambda: Decimal('0.00'))
    for txn in monthly_transaction:
        daily_data[txn.date.day] +=txn.amount

    # Prepare data for Chart.js
    chart_labels = list(range(1, num_days + 1))
    chart_data=[float(daily_data.get(day,0)) for day in chart_labels]



    # Customers assigned to agent
    customers = Customer.objects.filter(agent=agent)

    # Today's collections
    todays_collections = Transaction.objects.filter(agent=agent, date=today, transaction_type='deposit')
    todays_total = todays_collections.aggregate(total=Sum('amount'))['total'] or 0
    
    context = {
        'chart_labels': chart_labels,
        'chart_data': chart_data,
        'todays_total': daily_data.get(today.day, 0),
        'total_customers': customers.count(),
    }

    return render(request,"users/dashboard.html",context)

@login_required(login_url="login")
def customer_list(request):
    agent=request.user
    query=request.GET.get('q')
    customers=Customer.objects.filter(agent=agent).order_by('-id')

    if query:
        customers=Customer.objects.filter(
            Q(full_name__icontains=query)
        ).order_by('-id')

    # Pagination
    paginator=Paginator(customers,10)
    page_number=request.GET.get('page')
    page_obj=paginator.get_page(page_number)

    context={
        'page_obj':page_obj,
        'query':query or ''
    }
    
    return render(request,"customers/customer_list.html",context)

@login_required(login_url="login")
def collections_view(request):
    agent=request.user
    query=request.GET.get('q')
    saving_accounts=SavingAccount.objects.filter(customer__agent=agent)
    collections=Transaction.objects.filter(agent=agent).order_by('-id')

    if query:
        collections=Transaction.objects.filter(
            Q(agent=agent) & Q(saving_account__customer__full_name__icontains=query)
        ).order_by('-id')

    # Pagination
    paginator=Paginator(collections,25)
    page_number=request.GET.get('page')
    page_obj=paginator.get_page(page_number)

    context={
        'saving_accounts': saving_accounts,
        'page_obj':page_obj,
        'query':query or ''
    }

    return render(request,"accounts/collections_view.html",context)

@login_required(login_url="login")
def add_collection(request):
    agent=request.user
    if request.method == 'POST':
        account_id=request.POST.get('account_id')
        amount = request.POST.get('amount')
        remarks = request.POST.get('remarks')

        try:
            account=SavingAccount.objects.get(id=account_id)
        except SavingAccount.DoesNotExist:
            messages.error(request, 'Account not found.')
            return redirect('collections')

        Transaction.objects.create(
            saving_account=account,
            transaction_type='deposit',
            amount=amount,
            remarks=remarks,
            agent=agent
        )

        messages.success(request, 'Collection added successfully.')
        return redirect('collections')
