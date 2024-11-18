from rest_framework import serializers
from .models import BorrowedItem, InventoryItem

class BorrowedItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = BorrowedItem
        fields = ['id', 'item_name', 'item_quantity', 'borrower_name', 'borrower_first_name',
                 'borrower_last_name', 'borrower_middle_name', 'borrow_date', 'return_date', 'status']

class InventoryItemSerializer(serializers.ModelSerializer):
    available_quantity = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = InventoryItem
        fields = ['id', 'item_name', 'total_quantity', 'available_quantity']
