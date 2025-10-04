import pandas as pd
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from tracker.models import Category, Expense

class Command(BaseCommand):
    help = "Import expenses from an Excel file with columns 'Category' and 'Amount (NPR)'"

    def add_arguments(self, parser):
        parser.add_argument('username', help='Username to assign imported expenses to')
        parser.add_argument('path', help='Path to Excel file')

    def handle(self, *args, **opts):
        User = get_user_model()
        user = User.objects.get(username=opts['username'])
        df = pd.read_excel(opts['path'])
        count = 0
        for _, row in df.iterrows():
            cat_name = str(row.get('Category')).strip() if pd.notna(row.get('Category')) else 'Uncategorized'
            amount = row.get('Amount (NPR)')
            if pd.isna(amount):
                continue
            category, _ = Category.objects.get_or_create(name=cat_name)
            Expense.objects.create(user=user, category=category, amount=amount, description='Imported via command')
            count += 1
        self.stdout.write(self.style.SUCCESS(f'Imported {count} rows.'))
