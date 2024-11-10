from django.db import models
from django.contrib.auth.models import User

class BorrowedItem(models.Model):
    item_name = models.CharField(max_length=100)
    item_quantity = models.PositiveIntegerField()
    borrower_name = models.CharField(max_length=100)
    borrower_first_name = models.CharField(max_length=100)
    borrower_last_name = models.CharField(max_length=100)
    borrower_middle_name = models.CharField(max_length=100, blank=True)
    borrow_date = models.DateTimeField(auto_now_add=True)
    return_date = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=10, default='borrowed')  # borrowed or returned
    datenow = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.item_name} - {self.borrower_name}"
    
class InventoryItem(models.Model):
    item_name = models.CharField(max_length=100, unique=True)
    total_quantity = models.PositiveIntegerField()
    
    
    def available_quantity(self):
        # Calculate the quantity available for borrowing
        borrowed_quantity = BorrowedItem.objects.filter(
            item_name=self.item_name, status='borrowed'
        ).aggregate(models.Sum('item_quantity'))['item_quantity__sum'] or 0
        return self.total_quantity - borrowed_quantity

    def __str__(self):
        return f"{self.item_name} - Available: {self.available_quantity()}"
