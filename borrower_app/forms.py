from django import forms
from .models import BorrowedItem
from .models import InventoryItem

class InventoryItemForm(forms.ModelForm):
    class Meta:
        model = InventoryItem
        fields = ['item_name', 'total_quantity']
        labels = {
            'item_name': 'Item Name',
            'total_quantity': 'Quantity'
        }
    

class BorrowItemForm(forms.ModelForm):
    item_name = forms.ChoiceField(label="Item Name")
    item_quantity = forms.IntegerField(label="Quantity")
    borrower_first_name = forms.CharField(label='First Name')
    borrower_middle_name = forms.CharField(label='Middle Name')
    borrower_last_name = forms.CharField(label='Last Name')
    class Meta:
        model = BorrowedItem
        fields = ['borrower_last_name', 'borrower_first_name', 'borrower_middle_name', 'item_name', 'item_quantity']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Dynamically set choices to items available in inventory
        available_items = InventoryItem.objects.all()
        self.fields['item_name'].choices = [(item.item_name, item.item_name) for item in available_items]