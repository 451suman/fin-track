import csv, io
from datetime import date
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.db import models
import pandas as pd

from .models import Expense, Category, Account, Transaction
from .forms import AccountFormUpdate, ExpenseForm, CategoryForm, AccountForm, ExpenseUpdateForm, IncomeForm, TransferForm
from django.db.utils import OperationalError, ProgrammingError
from django.db import transaction

def login_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    form = AuthenticationForm(request, data=request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = authenticate(
            request,
            username=form.cleaned_data["username"],
            password=form.cleaned_data["password"],
        )
        if user:
            login(request, user)
            return redirect("dashboard")
        messages.error(request, "Invalid credentials")
    return render(request, "tracker/auth_login.html", {"form": form})


def logout_view(request):
    logout(request)
    return redirect("login")


def register_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    form = UserCreationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        messages.success(request, "Account created. Please log in.")
        return redirect("login")
    return render(request, "tracker/auth_register.html", {"form": form})


@login_required
def dashboard(request):
    try:
        qs = Expense.objects.filter(user=request.user)
    except (OperationalError, ProgrammingError):
        qs = Expense.objects.none()
    total = sum(x.amount for x in qs)
    by_cat = (
        qs.values("category__name", "category__color")
        .order_by("category__name")
        .annotate(total_amount=models.Sum("amount"))
    )
    labels = [x["category__name"] for x in by_cat]
    data = [float(x["total_amount"]) for x in by_cat]
    colors = [x["category__color"] or "#4fc3f7" for x in by_cat]
    recent = qs.select_related("category").order_by("-date", "-id")[:10]

    # Accounts and balances
    accounts = Account.objects.filter(user=request.user).order_by("name")
    return render(
        request,
        "tracker/dashboard.html",
        {
            "total": total,
            "labels": labels,
            "data": data,
            "colors": colors,
            "recent": recent,
            "accounts": accounts,
        },
    )


from django.utils.dateparse import parse_date  # ⬅ add at top with other imports


class ExpenseListView(LoginRequiredMixin, ListView):
    model = Expense
    template_name = "tracker/expense_list.html"
    paginate_by = 100
    def get_queryset(self):
        qs = Expense.objects.filter(user=self.request.user).select_related(
            "category", "account"
        )

        q = self.request.GET.get("q")
        cat = self.request.GET.get("category")
        acc = self.request.GET.get("account")

        # NEW: date range
        start = self.request.GET.get("start")  # e.g. '2025-10-03'
        end = self.request.GET.get("end")

        if q:
            qs = qs.filter(description__icontains=q)
        if cat:
            qs = qs.filter(category_id=cat)
        if acc:
            qs = qs.filter(account_id=acc)

        # Apply date range if provided
        if start:
            d = parse_date(start)
            if d:
                qs = qs.filter(date__gte=d)
        if end:
            d = parse_date(end)
            if d:
                qs = qs.filter(date__lte=d)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["categories"] = Category.objects.all()
        ctx["accounts"] = Account.objects.filter(user=self.request.user)
        return ctx


class ExpenseCreateView(LoginRequiredMixin, CreateView):
    model = Expense
    form_class = ExpenseForm
    success_url = reverse_lazy("expense_list")
    template_name = "tracker/expense_form.html"

    def form_valid(self, form):
        form.instance.user = self.request.user
        # account =form.instance.account
        # if account.balance < form.instance.amount:
        #     messages.error(self.request, f"Insufficient funds in Account: {account.name}")
        #     return redirect(self.success_url)
        
        # also create a Transaction (expense) affecting the chosen account
        try:
            # with transaction.atomic(): 
            expense = form.save()
                # if expense.account:
                #     Transaction.objects.create(
                #         user=self.request.user,
                #         account=expense.account,
                #         kind=Transaction.KIND_EXPENSE,
                #         category=expense.category,
                #         amount=expense.amount,
                #         date=expense.date,
                #         description=expense.description or f"Expense: {expense.category}",
                #         txn_uuid=expense.txn_uuid
                    # )
            messages.success(self.request, "Expense added.")
            return redirect(self.success_url)
        except Exception as e:
            messages.error(self.request, f"Error adding expense: {str(e)}")
            return redirect(self.success_url)



class ExpenseUpdateView(LoginRequiredMixin, UpdateView):
    model = Expense
    form_class = ExpenseUpdateForm
    success_url = reverse_lazy("expense_list")
    template_name = "tracker/expense_form.html"

    def get_queryset(self):
        return Expense.objects.filter(user=self.request.user)

    def form_valid(self, form):
        messages.success(self.request, "Expense updated.")
        return super().form_valid(form)


class ExpenseDeleteView(LoginRequiredMixin, DeleteView):
    model = Expense
    success_url = reverse_lazy("expense_list")
    template_name = "tracker/confirm_delete.html"

    def get_queryset(self):
        return Expense.objects.filter(user=self.request.user)


class CategoryListView(LoginRequiredMixin, ListView):
    model = Category
    template_name = "tracker/category_list.html"


class CategoryCreateView(LoginRequiredMixin, CreateView):
    model = Category
    form_class = CategoryForm
    success_url = reverse_lazy("category_list")
    template_name = "tracker/category_form.html"


class CategoryUpdateView(LoginRequiredMixin, UpdateView):
    model = Category
    form_class = CategoryForm
    success_url = reverse_lazy("category_list")
    template_name = "tracker/category_form.html"


class CategoryDeleteView(LoginRequiredMixin, DeleteView):
    model = Category
    success_url = reverse_lazy("category_list")
    template_name = "tracker/confirm_delete.html"


# Accounts
class AccountListView(LoginRequiredMixin, ListView):
    model = Account
    template_name = "tracker/account_list.html"

    def get_queryset(self):
        return Account.objects.filter(user=self.request.user)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        accounts = self.get_queryset()

        # Sum of actual balances (property calculation)
        total_balance = sum([acc.balance for acc in accounts])

        ctx["total"] = total_balance
        return ctx


class AccountCreateView(LoginRequiredMixin, CreateView):
    model = Account
    form_class = AccountForm
    success_url = reverse_lazy("account_list")
    template_name = "tracker/account_form.html"

    def form_valid(self, form):
        form.instance.user = self.request.user
        messages.success(self.request, "Account added.")
        return super().form_valid(form)


class AccountUpdateView(LoginRequiredMixin, UpdateView):
    model = Account
    form_class = AccountFormUpdate
    success_url = reverse_lazy("account_list")
    template_name = "tracker/account_form.html"

    def get_queryset(self):
        return Account.objects.filter(user=self.request.user)


class AccountDeleteView(LoginRequiredMixin, DeleteView):
    model = Account
    success_url = reverse_lazy("account_list")
    template_name = "tracker/confirm_delete.html"

    def get_queryset(self):
        return Account.objects.filter(user=self.request.user)


# Income and Transfers
@login_required
def add_income_view(request):
    form = IncomeForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        tx = form.save(commit=False)
        tx.user = request.user
        tx.kind = Transaction.KIND_INCOME
        tx.save()
        messages.success(request, "Income recorded.")
        return redirect("account_list")
    return render(request, "tracker/income_form.html", {"form": form})


@login_required
def transfer_view(request):
    form = TransferForm(request.POST or None, user=request.user)
    if request.method == "POST" and form.is_valid():
        from_account = form.cleaned_data["from_account"]
        to_account = form.cleaned_data["to_account"]
        amt = form.cleaned_data["amount"]
        desc = form.cleaned_data["description"]
        
        if from_account == to_account:
            messages.error(request, "Source and destination accounts cannot be the same.")
            return redirect("account_list")
        if from_account.balance < amt:
            messages.error(request, f"Insufficient funds in Account: {from_account.name} (Balance: {from_account.balance}) to transfer.")
            return redirect("account_list")

        # record as expense from src and income to dst
        Transaction.objects.create(
            user=request.user,
            account=from_account,
            kind=Transaction.KIND_EXPENSE,
            amount=amt,
            description=desc or f"Transfer to {to_account.name}",
        )
        Transaction.objects.create(
            user=request.user,
            account=to_account,
            kind=Transaction.KIND_INCOME,
            amount=amt,
            description=desc or f"Transfer from {from_account.name}",
        )
        messages.success(request, "Transfer completed.")
        return redirect("account_list")
    return render(request, "tracker/transfer_form.html", {"form": form})


@login_required
def import_excel_view(request):
    if request.method == "POST" and request.FILES.get("file"):
        file = request.FILES["file"]
        try:
            df = pd.read_excel(file)
            # Try to detect Accounts sheet-like columns first
            cols = [c.lower() for c in df.columns]
            if {"account", "type", "balance (npr)"}.issubset(set(cols)):
                # Import accounts with opening balances
                imported = 0
                for _, row in df.iterrows():
                    name = str(row.get("Account") or row.get("account")).strip()
                    typ = str(row.get("Type") or row.get("type")).strip().upper()
                    bal = row.get("Balance (NPR)") or 0
                    map_type = {"BANK": "BANK", "WALLET": "WALLET", "CASH": "CASH"}.get(
                        typ, "BANK"
                    )
                    acc, created = Account.objects.get_or_create(
                        user=request.user,
                        name=name,
                        defaults={"type": map_type, "opening_balance": bal or 0},
                    )
                    if not created:
                        acc.type = map_type
                        acc.opening_balance = bal or 0
                        acc.save()
                    imported += 1
                messages.success(request, f"Imported/updated {imported} accounts.")
                return redirect("account_list")
            else:
                # Fallback to Expenses import (Category, Amount (NPR))
                imported = 0
                for _, row in df.iterrows():
                    cat_name = (
                        str(row.get("Category")).strip()
                        if pd.notna(row.get("Category"))
                        else "Uncategorized"
                    )
                    amount = row.get("Amount (NPR)") or 0
                    if pd.isna(amount) or str(amount).strip() == "":
                        continue
                    category, _ = Category.objects.get_or_create(name=cat_name)
                    Expense.objects.create(
                        user=request.user,
                        category=category,
                        amount=amount,
                        description="Imported from Excel",
                    )
                    imported += 1
                messages.success(request, f"Imported {imported} expense rows.")
                return redirect("expense_list")
        except Exception as e:
            messages.error(request, f"Failed to import: {e}")
    return render(request, "tracker/import.html")


@login_required
def export_csv_view(request):
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = "attachment; filename=expenses.csv"
    writer = csv.writer(response)
    writer.writerow(["Date", "Category", "Amount", "Description"])
    for x in Expense.objects.filter(user=request.user).select_related("category"):
        writer.writerow([x.date, x.category.name, x.amount, x.description])
    return response


from django.shortcuts import get_object_or_404
from django.db import transaction as dbtx
from .models import Transaction, Person, Loan, LoanRepayment
from .forms import PersonForm, LoanForm, LoanRepaymentForm


# People
class PersonListView(LoginRequiredMixin, ListView):
    model = Person
    template_name = "tracker/person_list.html"

    def get_queryset(self):
        return Person.objects.filter(user=self.request.user)


class PersonCreateView(LoginRequiredMixin, CreateView):
    model = Person
    form_class = PersonForm
    template_name = "tracker/person_form.html"
    success_url = reverse_lazy("person_list")

    def form_valid(self, form):
        form.instance.user = self.request.user
        messages.success(self.request, "Person added.")
        return super().form_valid(form)


class PersonUpdateView(LoginRequiredMixin, UpdateView):
    model = Person
    form_class = PersonForm
    template_name = "tracker/person_form.html"
    success_url = reverse_lazy("person_list")

    def get_queryset(self):
        return Person.objects.filter(user=self.request.user)


class PersonDeleteView(LoginRequiredMixin, DeleteView):
    model = Person
    template_name = "tracker/confirm_delete.html"
    success_url = reverse_lazy("person_list")

    def get_queryset(self):
        return Person.objects.filter(user=self.request.user)


# Loans
class LoanListView(LoginRequiredMixin, ListView):
    model = Loan
    template_name = "tracker/loan_list.html"

    def get_queryset(self):
        qs = Loan.objects.filter(user=self.request.user).select_related(
            "person", "account"
        )
        direction = self.request.GET.get("direction")
        status = self.request.GET.get("status")
        if direction:
            qs = qs.filter(direction=direction)
        if status:
            qs = qs.filter(status=status)
        return qs


class LoanCreateView(LoginRequiredMixin, CreateView):
    model = Loan
    form_class = LoanForm
    template_name = "tracker/loan_form.html"
    success_url = reverse_lazy("loan_list")

    @dbtx.atomic
    def form_valid(self, form):
        # if form.instance.direction == Loan.DIR_LEND and form.instance.account.balance < form.instance.principal:
        #     messages.error(self.request, f"Insufficient funds in Account: {form.instance.account.name}")
        #     return redirect(self.success_url)
        
        # Ledger impact at creation:
        form.instance.user = self.request.user
        loan = form.save()

        # Ledger impact at creation:
        if loan.direction == Loan.DIR_LEND:
            # money goes OUT from my account
            Transaction.objects.create(
                user=self.request.user,
                account=loan.account,
                kind=Transaction.KIND_EXPENSE,
                amount=loan.principal,
                description=f"Loan to {loan.person.name}",
                date=loan.date,
            )
        else:
            # I borrowed => money comes IN to my account
            Transaction.objects.create(
                user=self.request.user,
                account=loan.account,
                kind=Transaction.KIND_INCOME,
                amount=loan.principal,
                description=f"Loan from {loan.person.name}",
                date=loan.date,
            )
        messages.success(self.request, "Loan recorded.")
        return super().form_valid(form)


class LoanUpdateView(LoginRequiredMixin, UpdateView):
    model = Loan
    form_class = LoanForm
    template_name = "tracker/loan_form.html"
    success_url = reverse_lazy("loan_list")

    def get_queryset(self):
        return Loan.objects.filter(user=self.request.user)


class LoanDetailView(LoginRequiredMixin, ListView):
    """Display one loan and its repayments."""

    template_name = "tracker/loan_detail.html"
    context_object_name = "repayments"

    def get_queryset(self):
        self.loan = get_object_or_404(
            Loan, pk=self.kwargs["pk"], user=self.request.user
        )
        return LoanRepayment.objects.filter(loan=self.loan)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["loan"] = self.loan
        ctx["form"] = LoanRepaymentForm()
        ctx["lend_or_borow"] = str(self.loan.direction).capitalize()
        return ctx


# @login_required
# @dbtx.atomic
# def add_repayment_view(request, pk):
#     loan = get_object_or_404(Loan, pk=pk, user=request.user)
#     form = LoanRepaymentForm(request.POST or None)
#     if request.method == "POST" and form.is_valid():
#         rep = form.save(commit=False)
#         rep.loan = loan
#         rep.save()
#         acc =  rep.account
#         # Ledger impact at repayment:
#         if loan.direction == Loan.DIR_LEND:
#             # I lent earlier, so repayment is INCOME to me
#             Transaction.objects.create(
#                 user=request.user,
#                 account=rep.account,
#                 kind=Transaction.KIND_INCOME,
#                 amount=rep.amount,
#                 description=f"Repayment from {loan.person.name}",
#                 date=rep.date,
#             )
#         else:
#             # I borrowed earlier, so repayment is EXPENSE for me
#             if acc.balance < rep.amount:
#                 messages.error(request, f"Insufficient funds in Account: {acc.name}")
#                 return redirect("loan_detail", pk=loan.pk)

#             # TODO: check if this is correct
#             Transaction.objects.create(
#                 user=request.user,
#                 account=rep.account,
#                 kind=Transaction.KIND_EXPENSE,
#                 amount=rep.amount,
#                 description=f"Repayment to {loan.person.name}",
#                 date=rep.date,
#             )

#         # Auto-close if fully repaid
#         if loan.outstanding <= 0 and loan.status != Loan.STATUS_CLOSED:
#             loan.status = Loan.STATUS_CLOSED
#             loan.save(update_fields=["status"])

#         messages.success(request, "Repayment added.")
#         return redirect("loan_detail", pk=loan.pk)
#     return render(
#         request,
#         "tracker/loan_detail.html",
#         {"loan": loan, "form": form, "repayments": loan.repayments.all()},
#     )

from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction as dbtx
from django.shortcuts import get_object_or_404, render, redirect

@login_required
@dbtx.atomic
def add_repayment_view(request, pk):
    loan = get_object_or_404(Loan, pk=pk, user=request.user)
    form = LoanRepaymentForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        rep = form.save(commit=False)
        rep.loan = loan
        acc = rep.account  # <-- Account instance already on the unsaved form object

        # If I borrowed earlier, paying back is an EXPENSE → ensure funds available
        if loan.direction == Loan.DIR_BORROW:
            if acc.balance < rep.amount:
                # Don't save anything; show error on the same page
                messages.error(request, f"Insufficient funds in account: {acc.name} (Balance: {acc.balance})")

                form.add_error(None, f"❌ Insufficient funds in account: {acc.name} (Balance: {acc.balance})")
                return render(
                    request,
                    "tracker/loan_detail.html",
                    {"loan": loan, "form": form, "repayments": loan.repayments.all()},
                    status=400,
                )

        # Create the ledger transaction first (so Account.balance reflects it)
        kind = (
            Transaction.KIND_INCOME
            if loan.direction == Loan.DIR_LEND
            else Transaction.KIND_EXPENSE
        )
        description = (
            f"Repayment from {loan.person.name}"
            if loan.direction == Loan.DIR_LEND
            else f"Repayment to {loan.person.name}"
        )
        Transaction.objects.create(
            user=request.user,
            account=acc,            # instance is fine
            kind=kind,
            amount=rep.amount,
            description=description,
            date=rep.date,
        )

        # Now persist the repayment
        rep.save()

        # Auto-close if fully repaid
        if loan.outstanding <= 0 and loan.status != Loan.STATUS_CLOSED:
            loan.status = Loan.STATUS_CLOSED
            loan.save(update_fields=["status"])

        messages.success(request, "Repayment added.")
        return redirect("loan_detail", pk=loan.pk)

    # GET or invalid POST
    return render(
        request,
        "tracker/loan_detail.html",
        {"loan": loan, "form": form, "repayments": loan.repayments.all()},
    )
