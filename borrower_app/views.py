from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import login, logout
from django.contrib import messages
from .models import BorrowedItem, InventoryItem
from .forms import BorrowItemForm, InventoryItemForm
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone 

# Register view
def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = UserCreationForm()
    return render(request, 'register.html', {'form': form})

# Login view
def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('home')
    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})

# Logout view
def logout_view(request):
    logout(request)
    return redirect('login')

# Homepage view (protected)
@login_required
def home(request):
    if request.method == 'POST':
        form = BorrowItemForm(request.POST)
        if form.is_valid():
            # Get the item name and quantity from the form
            item_name = form.cleaned_data['item_name']
            item_quantity = form.cleaned_data['item_quantity']
            # Fetch the actual InventoryItem instance by name
            try:
                inventory_item = InventoryItem.objects.get(item_name=item_name)
            except InventoryItem.DoesNotExist:
                form.add_error('item_name', "This item does not exist in the inventory.")
                return render(request, 'home.html', {'form': form})

            # Check if requested quantity is available
            if item_quantity > inventory_item.available_quantity():
                form.add_error(None, "Insufficient quantity available for borrowing.")
            else:
                # Sufficient inventory, proceed with borrowing
                borrowed_item = form.save(commit=False)
                borrowed_item.borrower_name = request.user.username
                borrowed_item.datenow = timezone.now()
                borrowed_item.save()
                return redirect('home')
    else:
        form = BorrowItemForm()

    # Get borrowed items for the current user
    items = BorrowedItem.objects.filter(borrower_name=request.user.username)
    return render(request, 'home.html', {'form': form, 'items': items})


# Return item view
@login_required
def return_item(request, item_id):
    try:
        item = BorrowedItem.objects.get(id=item_id, borrower_name=request.user.username)
        item.status = 'returned'
        item.return_date = timezone.now()
        item.save()
        return redirect('data_table')
    except BorrowedItem.DoesNotExist:
        return redirect('home')
    
# Delete item view
@login_required
def delete_item(request, item_id):
    item = get_object_or_404(BorrowedItem, id=item_id, borrower_name=request.user)
    item.delete()
    return redirect('data_table')

@login_required
def data_table_view(request):
    # Get all borrowed and returned items
    items = BorrowedItem.objects.all()  # This fetches both borrowed and returned items
    return render(request, 'data_table.html', {'items': items})

@login_required
def inventory_view(request):
    if request.method == 'POST':
        form = InventoryItemForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Item added to inventory.")
            return redirect('inventory')
        else:
            messages.error(request, "Error adding item. Please check the form.")
    else:
        form = InventoryItemForm()

    items = InventoryItem.objects.all()
    return render(request, 'inventory.html', {'items': items, 'form': form})

@login_required
def edit_inventory_item(request, item_id):
    item = get_object_or_404(InventoryItem, id=item_id)
    if request.method == 'POST':
        form = InventoryItemForm(request.POST, instance=item)
        if form.is_valid():
            form.save()
            messages.success(request, "Item updated successfully.")
            return redirect('inventory')
    else:
        form = InventoryItemForm(instance=item)
    return render(request, 'edit_inventory_item.html', {'form': form, 'item': item})

@login_required
def delete_inventory_item(request, item_id):
    item = get_object_or_404(InventoryItem, id=item_id)
    item.delete()
    messages.success(request, "Item deleted successfully.")
    return redirect('inventory')


def get_item_names(request):
    items = InventoryItem.objects.values_list('item_name', flat=True)
    return JsonResponse(list(items), safe=False)

