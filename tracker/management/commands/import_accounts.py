
import pandas as pd
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from tracker.models import Account

class Command(BaseCommand):
    help = "Import accounts from Excel with columns: Account, Type, Balance (NPR)"

    def add_arguments(self, parser):
        parser.add_argument('username', help='Username that owns the accounts')
        parser.add_argument('path', help='Path to Excel file')

    def handle(self, *args, **opts):
        User = get_user_model()
        user = User.objects.get(username=opts['username'])
        df = pd.read_excel(opts['path'])
        count = 0
        for _, row in df.iterrows():
            name = str(row.get('Account')).strip()
            typ = str(row.get('Type')).strip().upper()
            bal = row.get('Balance (NPR)') or 0
            map_type = {'BANK':'BANK','WALLET':'WALLET','CASH':'CASH'}.get(typ, 'BANK')
            acc, created = Account.objects.get_or_create(user=user, name=name, defaults={'type': map_type, 'opening_balance': bal})
            if not created:
                acc.type = map_type
                acc.opening_balance = bal
                acc.save()
            count += 1
        self.stdout.write(self.style.SUCCESS(f'Imported/updated {count} accounts.'))
