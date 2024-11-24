from django import forms
from .models import BorrowedItem, InventoryItem

class InventoryItemForm(forms.ModelForm):
    class Meta:
        model = InventoryItem
        fields = ['item_name', 'total_quantity', 'low_stock_threshold']
        labels = {
            'item_name': 'Item Name',
            'total_quantity': 'Total Quantity',
            'low_stock_threshold': 'Low Stock Alert Threshold'
        }
        widgets = {
            'item_name': forms.TextInput(attrs={
                'class': 'form-control text-capitalize',
                'placeholder': 'Enter Item Name',
                'pattern': '[A-Za-z0-9 ]+',
                'title': 'Only letters, numbers, and spaces are allowed'
            }),
            'total_quantity': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter Total Quantity',
                'min': '0'
            }),
            'low_stock_threshold': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter Low Stock Threshold',
                'min': '1'
            })
        }

    def clean_item_name(self):
        return self.cleaned_data['item_name'].title()

    def clean(self):
        cleaned_data = super().clean()
        total_quantity = cleaned_data.get('total_quantity')
        low_stock_threshold = cleaned_data.get('low_stock_threshold')

        if total_quantity is not None and low_stock_threshold is not None:
            if low_stock_threshold > total_quantity:
                raise forms.ValidationError(
                    "Low stock threshold cannot be greater than total quantity."
                )
        return cleaned_data


class BorrowItemForm(forms.ModelForm):
    item_name = forms.ChoiceField(
        label='Item Name',
        choices=[],
        widget=forms.Select(attrs={
            'class': 'form-control form-select',
            'placeholder': 'Select Item Name'
        })
    )

    class Meta:
        model = BorrowedItem
        fields = ['borrower_last_name', 'borrower_first_name', 'borrower_middle_name', 'item_name', 'item_quantity']
        labels = {
            'borrower_first_name': 'First Name',
            'borrower_middle_name': 'Middle Name',
            'borrower_last_name': 'Last Name',
            'item_quantity': 'Quantity'
        }
        widgets = {
            'borrower_first_name': forms.TextInput(attrs={
                'class': 'form-control text-capitalize',
                'placeholder': 'Enter First Name',
                'pattern': '[A-Za-z ]+',
                'title': 'Only letters and spaces are allowed'
            }),
            'borrower_middle_name': forms.TextInput(attrs={
                'class': 'form-control text-capitalize',
                'placeholder': 'Enter Middle Name',
                'pattern': '[A-Za-z ]+',
                'title': 'Only letters and spaces are allowed'
            }),
            'borrower_last_name': forms.TextInput(attrs={
                'class': 'form-control text-capitalize',
                'placeholder': 'Enter Last Name',
                'pattern': '[A-Za-z ]+',
                'title': 'Only letters and spaces are allowed'
            }),
            'item_quantity': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter Quantity',
                'min': '1'
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Dynamically set choices to items available in inventory
        available_items = InventoryItem.objects.all()
        self.fields['item_name'].choices = [('', '---SELECT ITEM---')] + [
            (item.item_name, f"{item.item_name} ({item.available_quantity()} available)") 
            for item in available_items
        ]

    def clean_borrower_first_name(self):
        return self.cleaned_data['borrower_first_name'].title()

    def clean_borrower_middle_name(self):
        middle_name = self.cleaned_data.get('borrower_middle_name', '')
        return middle_name.title() if middle_name else ''

    def clean_borrower_last_name(self):
        return self.cleaned_data['borrower_last_name'].title()