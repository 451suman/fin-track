from datetime import timezone
from django import forms
from .models import Expense, Category, Account, Transaction

class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = ['date', 'account', 'category', 'amount', 'description']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'account': forms.Select(attrs={'class': 'form-select'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'description': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Optional note'}),
        }
    def clean(self):
        cleaned_data = super().clean()
        account = cleaned_data.get('account')
        amount = cleaned_data.get('amount')
        date = cleaned_data.get('date')
        if account.balance < amount:
            raise forms.ValidationError({
                'account': f"❌ Insufficient funds in Account: {account.name} (Balance: {account.balance})"
            })
        if amount <= 0:
            raise forms.ValidationError({
                'amount': f"❌ Amount must be greater than 0."
            })

        return cleaned_data


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'color']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'color': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '#4fc3f7'}),
        }

class AccountForm(forms.ModelForm):
    class Meta:
        model = Account
        fields = ['name', 'type', 'opening_balance']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'type': forms.Select(attrs={'class': 'form-select'}),
            'opening_balance': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }

class IncomeForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ['date', 'account', 'amount', 'description', 'category']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'account': forms.Select(attrs={'class': 'form-select'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'description': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Note (optional)'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
        }

class TransferForm(forms.Form):
    date = forms.DateInput
    from_account = forms.ModelChoiceField(queryset=Account.objects.none(), widget=forms.Select(attrs={'class':'form-select'}))
    to_account = forms.ModelChoiceField(queryset=Account.objects.none(), widget=forms.Select(attrs={'class':'form-select'}))
    amount = forms.DecimalField(decimal_places=2, max_digits=14, widget=forms.NumberInput(attrs={'class':'form-control','step':'0.01'}))
    description = forms.CharField(required=False, widget=forms.TextInput(attrs={'class':'form-control','placeholder':'Note (optional)'}))

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields['from_account'].queryset = Account.objects.filter(user=user)
            self.fields['to_account'].queryset = Account.objects.filter(user=user)

    def clean(self):
        cleaned = super().clean()
        if cleaned.get('from_account') == cleaned.get('to_account'):
            raise forms.ValidationError("Choose two different accounts for a transfer.")
        return cleaned


from django import forms
from .models import Person, Loan, LoanRepayment

class PersonForm(forms.ModelForm):
    class Meta:
        model = Person
        fields = ['name', 'phone', 'note']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'note': forms.TextInput(attrs={'class': 'form-control'}),
        }

class LoanForm(forms.ModelForm):
    class Meta:
        model = Loan
        fields = ['person', 'direction', 'principal', 'date', 'due_date', 'interest_rate', 'account', 'description', 'status']
        widgets = {
            'person': forms.Select(attrs={'class': 'form-select'}),
            'direction': forms.Select(attrs={'class': 'form-select'}),
            'principal': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'due_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'interest_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'account': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.TextInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }
    def clean(self):
        cleaned_data = super().clean()
        direction = cleaned_data.get('direction')
        principal = cleaned_data.get('principal')
        account = cleaned_data.get('account')
        if direction == Loan.DIR_LEND and account and principal:
            if account.balance < principal:
                raise forms.ValidationError({
                    'account': f"❌ Insufficient funds in Account: {account.name} (Balance: {account.balance})"
                })
        return cleaned_data
class LoanRepaymentForm(forms.ModelForm):
    class Meta:
        model = LoanRepayment
        fields = ['date', 'amount', 'account', 'note']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'account': forms.Select(attrs={'class': 'form-select'}),
            'note': forms.TextInput(attrs={'class': 'form-control'}),
        }
