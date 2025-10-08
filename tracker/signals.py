from django.db.models.signals import post_save
from django.dispatch import receiver

from tracker.models import Expense, Transaction

@receiver(post_save, sender=Expense)
def update_transaction_amount(sender, instance, created, **kwargs):
    if created:
        Transaction.objects.create(
                        user=instance.user,
                        account=instance.account,
                        kind=Transaction.KIND_EXPENSE,
                        category=instance.category,
                        amount=instance.amount,
                        date=instance.date,
                        description=instance.description or f"Expense: {instance.category}",
                        txn_uuid=instance.txn_uuid
                    )
    else:
        txn = instance.txn_uuid
        if txn:
            txn_obj = Transaction.objects.get(txn_uuid=txn)
            txn_obj.amount = instance.amount
            txn_obj.save()
        