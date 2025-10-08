from datetime import date
import datetime
import uuid
import nepali_datetime
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models import Sum, F, Q
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

from tracker.common import generate_transactions_ref
class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    color = models.CharField(
        max_length=7, default="#4fc3f7", help_text="Hex color like #4fc3f7"
    )

    def __str__(self):
        return self.name


class Account(models.Model):
    TYPE_BANK = "BANK"
    TYPE_WALLET = "WALLET"
    TYPE_CASH = "CASH"
    TYPE_CHOICES = [
        (TYPE_BANK, "Bank"),
        (TYPE_WALLET, "Wallet"),
        (TYPE_CASH, "Cash"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="accounts")
    name = models.CharField(max_length=120)
    type = models.CharField(max_length=10, choices=TYPE_CHOICES, default=TYPE_BANK)
    opening_balance = models.DecimalField(max_digits=14, decimal_places=2, default=0)

    class Meta:
        unique_together = ("user", "name")
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.get_type_display()})"

    @property
    def balance(self):
        # opening + income - expense
        totals = self.transactions.aggregate(
            income=Sum("amount", filter=Q(kind=Transaction.KIND_INCOME)),
            expense=Sum("amount", filter=Q(kind=Transaction.KIND_EXPENSE)),
        )
        income = totals.get("income") or 0
        expense = totals.get("expense") or 0
        return self.opening_balance + income - expense

# keep transaction with loan and repayment
class Transaction(models.Model):
    KIND_INCOME = "INCOME"
    KIND_EXPENSE = "EXPENSE"
    KIND_CHOICES = [
        (KIND_INCOME, "Income"),
        (KIND_EXPENSE, "Expense"),
    ]

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="transactions"
    )
    account = models.ForeignKey(
        Account, on_delete=models.CASCADE, related_name="transactions"
    )
    kind = models.CharField(max_length=10, choices=KIND_CHOICES, default=KIND_EXPENSE)
    category = models.ForeignKey(
        "Category",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="transactions",
    )
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    date = models.DateField(default=timezone.now)
    description = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    txn_uuid =models.CharField(
        max_length=100, unique=True, editable=False, blank=True, null=True , 
    )

    class Meta:
        ordering = ["-date", "-id"]

    def __str__(self):
        return f"{self.kind} {self.amount} on {self.account}"



# Keep Expense for backward-compat (used by existing views), but now link to Account.
# keep transaction except loan and repayment
class Expense(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="expenses")
    category = models.ForeignKey(
        Category, on_delete=models.PROTECT, related_name="expenses"
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    date = models.DateField(default=timezone.now)
    account = models.ForeignKey(
        Account,
        on_delete=models.CASCADE,
        related_name="expenses",
        null=True,
        blank=True,
    )
    description = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    txn_uuid =models.CharField(
        max_length=100, unique=True, editable=False, blank=True, null=True
    )
    

    class Meta:
        ordering = ["-date", "-id"]

    def __str__(self):
        return f"{self.category} - {self.amount}"
    def save(self, *args, **kwargs):
        if not self.txn_uuid:
            self.txn_uuid = generate_transactions_ref("TXN")
        super().save(*args, **kwargs)
    

    
    @property
    def nepali_date(self):
        """Return transaction date (A.D → B.S)."""
        if self.date:
            return nepali_datetime.date.from_datetime_date(self.date)
        return None

    @property
    def nepali_created_at(self):
        """Return created_at datetime (A.D → B.S)."""
        if self.created_at:
            return nepali_datetime.datetime.from_datetime_datetime(self.created_at)
        return None


# === Loans / Borrowings ===



class Person(models.Model):
    """Someone you lend/borrow money with."""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="people")
    name = models.CharField(max_length=120)
    phone = models.CharField(max_length=30, blank=True)
    note = models.CharField(max_length=255, blank=True)

    class Meta:
        unique_together = ("user", "name")
        ordering = ["name"]

    def __str__(self):
        return self.name


class Loan(models.Model):
    """A single loan agreement."""

    DIR_LEND = "LEND"  # I gave money to someone -> receivable
    DIR_BORROW = "BORROW"  # I took money from someone -> payable
    DIR_CHOICES = [
        (DIR_LEND, "I lent"),
        (DIR_BORROW, "I borrowed"),
    ]

    STATUS_OPEN = "OPEN"
    STATUS_CLOSED = "CLOSED"
    STATUS_CHOICES = [
        (STATUS_OPEN, "Open"),
        (STATUS_CLOSED, "Closed"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="loans")
    person = models.ForeignKey(Person, on_delete=models.PROTECT, related_name="loans")
    direction = models.CharField(max_length=10, choices=DIR_CHOICES, default=DIR_LEND)
    principal = models.DecimalField(max_digits=14, decimal_places=2)
    date = models.DateField(default=timezone.now)
    due_date = models.DateField(null=True, blank=True)
    interest_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        help_text="Annual % (optional). Leave 0 if not used.",
    )
    account = models.ForeignKey(
        "Account",
        on_delete=models.PROTECT,
        related_name="loans",
        help_text="Account money goes from/to at loan creation.",
    )
    description = models.CharField(max_length=255, blank=True)
    status = models.CharField(
        max_length=10, choices=STATUS_CHOICES, default=STATUS_OPEN
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date", "-id"]

    def __str__(self):
        who = "to" if self.direction == self.DIR_LEND else "from"
        return f"{self.get_direction_display()} {self.person.name} ({who} {self.person.name})"

    @property
    def repaid_amount(self):
        agg = self.repayments.aggregate(total=Sum("amount"))
        return agg["total"] or 0

    @property
    def outstanding(self):
        # ignore interest math for simplicity; can extend later
        return self.principal - self.repaid_amount

    @property
    def nepali_due_date(self):
        """Return due_date converted to Nepali date (B.S)."""
        if self.due_date:
            return nepali_datetime.date.from_datetime_date(self.due_date)
        return None

    @property
    def nepali_date(self):
        """Return transaction date (A.D → B.S)."""
        if self.date:
            return nepali_datetime.date.from_datetime_date(self.date)
        return None
    
    @property
    def due_status(self):
        """Return status based on comparison of due_date and today's date."""
        today = date.today()
        if not self.due_date:
            return "-"
        if self.due_date < today:
            return "Overdue"
        elif self.due_date == today:
            return "Due Today"
        else:
            return "Upcoming"
    

class LoanRepayment(models.Model):
    """Each repayment for a loan."""

    loan = models.ForeignKey(Loan, on_delete=models.CASCADE, related_name="repayments")
    date = models.DateField(default=timezone.now)
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    account = models.ForeignKey(
        "Account", on_delete=models.PROTECT, related_name="loan_repayments"
    )
    note = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date", "-id"]

    def __str__(self):
        return f"{self.amount} on {self.date} for {self.loan_id}"
