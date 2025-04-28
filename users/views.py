from django.shortcuts import render,redirect
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
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
    year, month = today.year, today.month
    num_days = calendar.monthrange(year, month)[1]

    start_date = date(year, month, 1)
    end_date = date(year, month, num_days)

    # Fetch monthly transactions
    monthly_transaction = Transaction.objects.filter(
        transaction_type="deposit",
        date__range=(start_date, end_date),
        **({} if request.user.role == 'admin' else {'agent': agent})
    )

    # Calculate daily deposit data
    daily_data = defaultdict(lambda: Decimal('0.00'))
    for txn in monthly_transaction:
        daily_data[txn.date.day] += txn.amount

    # Prepare Chart.js data
    chart_labels = list(range(1, num_days + 1))
    chart_data = [float(daily_data.get(day, 0)) for day in chart_labels]

    # Monthly collection total
    monthly_total = sum(daily_data.values())

    # Customers assigned
    customers = SavingAccount.objects.filter(
        **({} if request.user.role == 'admin' else {'agent': agent})
    )

    context = {
        'chart_labels': chart_labels,
        'chart_data': chart_data,
        'todays_total': float(daily_data.get(today.day, 0)),
        'monthly_total': float(monthly_total),
        'total_customers': customers.count(),
    }

    return render(request,"users/dashboard.html",context)

@login_required(login_url="login")
def customer_list(request):
    agent=request.user
    query=request.GET.get('q')
    customers=SavingAccount.objects.filter(
            **({} if request.user.role == 'admin' else {'agent': agent})
        ).order_by('-id')

    if query:
        customers=SavingAccount.objects.filter(
            Q(full_name__icontains=query),
        **({} if request.user.role == 'admin' else {'agent': agent})
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
    saving_accounts=SavingAccount.objects.filter(agent=agent)
    collections=Transaction.objects.filter(
        **({} if request.user.role == 'admin' else {'agent': agent})
    ).order_by('-id')

    if query:
        collections=Transaction.objects.filter(
            Q(agent=agent) & Q(saving_account__full_name__icontains=query),
            **({} if request.user.role == 'admin' else {'agent': agent})
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
