from django.urls import path
from . import views

urlpatterns = [
    path("dashboard/", views.dashboard, name="dashboard"),
    path("expenses/", views.ExpenseListView.as_view(), name="expense_list"),
    path("expenses/create/", views.ExpenseCreateView.as_view(), name="expense_create"),
    path(
        "expenses/<int:pk>/update/",
        views.ExpenseUpdateView.as_view(),
        name="expense_update",
    ),
    path(
        "expenses/<int:pk>/delete/",
        views.ExpenseDeleteView.as_view(),
        name="expense_delete",
    ),
    path("categories/", views.CategoryListView.as_view(), name="category_list"),
    path(
        "categories/create/", views.CategoryCreateView.as_view(), name="category_create"
    ),
    path(
        "categories/<int:pk>/update/",
        views.CategoryUpdateView.as_view(),
        name="category_update",
    ),
    path(
        "categories/<int:pk>/delete/",
        views.CategoryDeleteView.as_view(),
        name="category_delete",
    ),
    path("accounts/", views.AccountListView.as_view(), name="account_list"),
    path("accounts/create/", views.AccountCreateView.as_view(), name="account_create"),
    path(
        "accounts/<int:pk>/update/",
        views.AccountUpdateView.as_view(),
        name="account_update",
    ),
    path(
        "accounts/<int:pk>/delete/",
        views.AccountDeleteView.as_view(),
        name="account_delete",
    ),
    path("income/add/", views.add_income_view, name="income_add"),
    path("transfer/", views.transfer_view, name="transfer"),
    path("import/", views.import_excel_view, name="import_excel"),
    path("export/csv/", views.export_csv_view, name="export_csv"),
    path("auth/login/", views.login_view, name="login"),
    path("auth/logout/", views.logout_view, name="logout"),
    path("auth/register/", views.register_view, name="register"),
    # People
    path("people/", views.PersonListView.as_view(), name="person_list"),
    path("people/create/", views.PersonCreateView.as_view(), name="person_create"),
    path(
        "people/<int:pk>/update/",
        views.PersonUpdateView.as_view(),
        name="person_update",
    ),
    path(
        "people/<int:pk>/delete/",
        views.PersonDeleteView.as_view(),
        name="person_delete",
    ),
    # Loans
    path("loans/", views.LoanListView.as_view(), name="loan_list"),
    path("loans/create/", views.LoanCreateView.as_view(), name="loan_create"),
    path("loans/<int:pk>/update/", views.LoanUpdateView.as_view(), name="loan_update"),
    path("loans/<int:pk>/", views.LoanDetailView.as_view(), name="loan_detail"),
    path("loans/<int:pk>/repay/", views.add_repayment_view, name="loan_repay"),
]
