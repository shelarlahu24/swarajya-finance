# Generated by Django 5.2 on 2025-04-27 15:40

from decimal import Decimal
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='FinanceSettings',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('minimum_active_days', models.PositiveIntegerField(default=90)),
                ('loan_eligible_days', models.PositiveIntegerField(default=45)),
                ('commission_deducted', models.DecimalField(decimal_places=2, default=Decimal('3.00'), help_text='Commission (%) for < minimum_active_days', max_digits=5)),
                ('interest_earn', models.DecimalField(decimal_places=2, default=Decimal('4.00'), help_text='Interest (%) for ≥ minimum_active_days', max_digits=5)),
                ('agent_commission_rate', models.DecimalField(decimal_places=2, default=Decimal('3.00'), help_text='Agent get commission after 1 month', max_digits=5)),
            ],
            options={
                'verbose_name': 'Finance Setting',
                'verbose_name_plural': 'Finance Settings',
            },
        ),
    ]
