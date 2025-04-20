from datetime import date, timedelta
from decimal import Decimal
from django.db.models import Sum
from .models import AgentCommission, Transaction
from django.contrib.auth.models import User

def calculate_commissions_for_month(month_start):
    month_end = (month_start.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)

    agents = User.objects.filter(groups__name='Agent')
    
    for agent in agents:
        total_collected = Transaction.objects.filter(
            agent=agent,
            transaction_type='deposit',
            date__range=(month_start, month_end)
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

        commission_amount = total_collected * Decimal('0.03')

        commission, created = AgentCommission.objects.update_or_create(
            agent=agent,
            month=month_start,
            defaults={
                'total_collection': total_collected,
                'commission': commission_amount
            }
        )
