# from django.db.models.signals import post_save
# from django.dispatch import receiver

# from tracker.models import Expense, Transaction

# @receiver(post_save, sender=Expense)
# def update_transaction_amount(sender, instance, created, **kwargs):
#     if created:
#         Transaction.objects.create(
#                         user=instance.user,
#                         account=instance.account,
#                         kind=Transaction.KIND_EXPENSE,
#                         category=instance.category,
#                         amount=instance.amount,
#                         date=instance.date,
#                         description=instance.description or f"Expense: {instance.category}",
#                         txn_uuid=instance.txn_uuid
#                     )
#     else:
#         txn = instance.txn_uuid
#         if txn:
#             txn_obj = Transaction.objects.get(txn_uuid=txn)
#             txn_obj.amount = instance.amount
#             txn_obj.category = instance.category
#             txn_obj.description = instance.description
#             txn_obj.date = instance.date
#             txn_obj.save()
        
from django.db.models.signals import post_save
from django.dispatch import receiver
from tracker.models import Expense, Transaction

@receiver(post_save, sender=Expense)
def update_transaction_amount(sender, instance, created, **kwargs):
    if created:
        # Create new transaction for the newly created expense
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
        if instance.txn_uuid:
            try:
                txn_obj = Transaction.objects.get(txn_uuid=instance.txn_uuid)
                # Update existing transaction
                txn_obj.amount = instance.amount
                txn_obj.category = instance.category
                txn_obj.description = instance.description
                txn_obj.date = instance.date
                txn_obj.save()
            except Transaction.DoesNotExist:
                # Either skip or create the missing transaction
                find_txn = Transaction.objects.get(
                    user = instance.user,
                    account = instance.account,
                    kind = Transaction.KIND_EXPENSE,
                    category = instance.category,
                    description = instance.description 
                )
                find_txn.txn_uuid = instance.txn_uuid
                find_txn.save()
                # Transaction.objects.create(
                #     user=instance.user,
                #     account=instance.account,
                #     kind=Transaction.KIND_EXPENSE,
                #     category=instance.category,
                #     amount=instance.amount,
                #     date=instance.date,
                #     description=instance.description or f"Expense: {instance.category}",
                #     txn_uuid=instance.txn_uuid
                # )
