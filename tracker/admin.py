from django.contrib import admin
from .models import Category, Expense, Account, Transaction, Person, Loan, LoanRepayment

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'color')
    search_fields = ('name',)

@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ('name', 'type', 'balance', 'user')
    list_filter = ('type',)
    search_fields = ('name',)

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ("id",'date',"txn_uuid", 'kind', 'account', 'amount', 'category', 'user', 'description')
    list_filter = ('kind', 'account', 'category', 'date')
    search_fields = ('description',"txn_uuid",)
    

@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ("id",'date',"txn_uuid", 'category', 'amount', 'account', 'user', 'description')
    list_filter = ('category', 'date', 'user')
    search_fields = ('description',"txn_uuid",)




@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'user')
    search_fields = ('name', 'phone')

@admin.register(Loan)
class LoanAdmin(admin.ModelAdmin):
    list_display = ('person', 'direction', 'principal', 'outstanding', 'status', 'date', 'due_date', 'account', 'user')
    list_filter = ('direction', 'status')
    search_fields = ('person__name', 'description')

@admin.register(LoanRepayment)
class LoanRepaymentAdmin(admin.ModelAdmin):
    list_display = ('loan', 'amount', 'date', 'account')
    list_filter = ('date',)
