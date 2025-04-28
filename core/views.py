# core/admin_dashboard.py
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.template.response import TemplateResponse
from django.db.models import Sum
from calendar import monthrange
from django.db.models.functions import TruncDay
from datetime import timedelta
from django.utils.timezone import now
from accounts.models import SavingAccount, Transaction

User=get_user_model()

def custom_admin_index(request):
    today = now().date()
    first_day = today.replace(day=1)
    last_day = today.replace(day=monthrange(today.year, today.month)[1])

    # Step 1: Create list of all days in current month
    all_days = [first_day + timedelta(days=i) for i in range((last_day - first_day).days + 1)]
    day_labels = [d.strftime('%d %b') for d in all_days]

    # Step 2: Get actual collection data from DB
    collection_data = (
        Transaction.objects
        .filter(transaction_type='deposit', date__range=(first_day, last_day))
        .annotate(day=TruncDay('date'))
        .values('day')
        .annotate(total=Sum('amount'))
        .order_by('day')
    )

    collection_dict = {item['day']: float(item['total']) for item in collection_data}

    # Step 3: Create full list with 0 fallback
    collections = [collection_dict.get(d, 0) for d in all_days]

    
    total_customers = SavingAccount.objects.all()
    total_agents = User.objects.filter(role='agent')
    todays_collection = Transaction.objects.filter(date=today, transaction_type='deposit').aggregate(Sum('amount'))['amount__sum'] or 0
    monthly_collection = Transaction.objects.filter(date__month=today.month, transaction_type='deposit').aggregate(Sum('amount'))['amount__sum'] or 0

    context = admin.site.each_context(request)  # base context
    context.update({
        "days": day_labels,
        "collections": collections,
        "now": now(),
        "total_customers": total_customers.count(),
        "total_agents" : total_agents.count(),
        "todays_collection": todays_collection,
        "monthly_collection": monthly_collection,
        "app_list": admin.site.get_app_list(request),  # ✅ important line!
    })

    return TemplateResponse(request, "admin/index.html", context)
