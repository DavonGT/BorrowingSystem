from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import login, logout
from django.contrib import messages
from .models import BorrowedItem, InventoryItem
from .forms import BorrowItemForm, InventoryItemForm
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone 
import subprocess
import cv2
from django.db.models import Sum
from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .serializers import BorrowedItemSerializer, InventoryItemSerializer
from datetime import timedelta
import platform
if platform.system() == "Windows":
    import win32com.client
    import pythoncom
    import comtypes.client
    import comtypes
import os
from .models import InventoryItem
from django.core.files.storage import FileSystemStorage


@login_required
def home(request):
    """
    Homepage view, handles borrowing of items and displays alerts.
    """
    total_borrowers = BorrowedItem.objects.values(
        'borrower_first_name', 'borrower_last_name', 'borrower_middle_name'
    ).distinct().count()

    total_borrowed_items = BorrowedItem.objects.filter(status='borrowed').aggregate(Sum('item_quantity'))['item_quantity__sum'] or 0
    total_returned_items = BorrowedItem.objects.filter(status='returned').aggregate(Sum('item_quantity'))['item_quantity__sum'] or 0

    # Get low stock items
    low_stock_items = [item for item in InventoryItem.objects.all() if item.is_low_stock()]
    
    # Get overdue items
    seven_days_ago = timezone.now() - timedelta(days=7)
    overdue_items = BorrowedItem.objects.filter(
        borrow_date__lt=seven_days_ago,
        status='borrowed'
    )

    if request.method == 'POST':
        form = BorrowItemForm(request.POST)
        if form.is_valid():
            item_name = form.cleaned_data['item_name']
            item_quantity = form.cleaned_data['item_quantity']
            try:
                inventory_item = InventoryItem.objects.get(item_name=item_name)
            except InventoryItem.DoesNotExist:
                form.add_error('item_name', "This item does not exist in the inventory.")
                return render(request, 'home.html', {
                    'form': form, 'total_borrowers': total_borrowers,
                    'total_borrowed_items': total_borrowed_items, 'total_returned_items': total_returned_items,
                    'low_stock_items': low_stock_items, 'overdue_items': overdue_items
                })

            available_quantity = inventory_item.available_quantity()
            if item_quantity > available_quantity:
                form.add_error(None, f"Only {available_quantity} item(s) available for borrowing.")
                return render(request, 'home.html', {
                    'form': form, 'total_borrowers': total_borrowers,
                    'total_borrowed_items': total_borrowed_items, 'total_returned_items': total_returned_items,
                    'low_stock_items': low_stock_items, 'overdue_items': overdue_items
                })

            borrowed_item = form.save(commit=False)
            borrowed_item.borrower_name = request.user.username
            borrowed_item.borrow_date = timezone.now()
            borrowed_item.save()
            inventory_item.save()
            
            # Check if borrowing this item will trigger low stock alert
            if inventory_item.is_low_stock():
                messages.warning(request, f'Warning: {inventory_item.item_name} is now low in stock!')
            
            return redirect('home')
    else:
        form = BorrowItemForm()

    borrowed_items = BorrowedItem.objects.filter(borrower_name=request.user.username)

    context = {
        'form': form,
        'borrowed_items': borrowed_items,
        'total_borrowers': total_borrowers,
        'total_borrowed_items': total_borrowed_items,
        'total_returned_items': total_returned_items,
        'low_stock_items': low_stock_items,
        'overdue_items': overdue_items,
    }
    return render(request, 'home.html', context)


# Register view
def register_view(request):
    """
    View for user registration.
    """
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = UserCreationForm()
    context = {'form': form}
    return render(request, 'register.html', context)

# Login view
def login_view(request):
    if request.method == 'POST':
        auth_form = AuthenticationForm(data=request.POST)
        if auth_form.is_valid():
            user = auth_form.get_user()
            login(request, user)
            return redirect('home')
        else:
            # Override error messages
            for field in auth_form:
                if field.errors:
                    if field.name == 'username':
                        field.errors = ['Please Enter Correct Usernama']
                    elif field.name == 'password':
                        field.errors = ['Please Enter Correct Password']
    else:
        auth_form = AuthenticationForm()

    context = {'form': auth_form}
    return render(request, 'login.html', context)


# Logout view
def logout_view(request):
    logout(request)
    return redirect('login')

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
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True})
            messages.success(request, "Item added to inventory.")
            return redirect('inventory')
        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'errors': {field: errors for field, errors in form.errors.items()}
                })
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
            error_message = form.errors.as_text()
            messages.error(request, f"Error updating item: {error_message}")
    return redirect('inventory')

@login_required
def delete_inventory_item(request, item_id):
    item = get_object_or_404(InventoryItem, id=item_id)
    item.delete()
    messages.success(request, "Item deleted successfully.")
    return redirect('inventory')


def get_item_names(request):
    items = InventoryItem.objects.values_list('item_name', flat=True)
    return JsonResponse(list(items), safe=False)

# @csrf_exempt
# def scan_paper(request):
#     image_path = 'HTR/scannedImages/scanned_form.png'
#     with open(image_path, 'wb') as f:
#         is_scan = subprocess.run('scanimage --format=png --mode Color --resolution 600', stdout=f, shell=True)
#         if is_scan.returncode != 0:
#             # Cropping the scanned image
#             image = cv2.imread(image_path)
#             h, w, _ = image.shape
#             image = image[:h // 2, :w//2]
#             cv2.imwrite(image_path, image)

#             # Doing now the actual scanning
#             scan = subprocess.run(f'python3 HTR/ocr.py {image_path}', shell=True)
#             if scan.returncode == 0:
#                 return HttpResponse('Scanned')
#             else:
#                 return HttpResponse('Not Scanned')
    
#     return HttpResponse('Scan Complete.')


# @csrf_exempt
# def scan_paper(request):
#     image_path = 'HTR/scannedImages/scanned_form.png'
#     with open(image_path, 'wb') as f:
#         is_scan = subprocess.run('scanimage --format=png --mode Color --resolution 600', stdout=f, shell=True)
#         if is_scan.returncode != 0:
#             # Cropping the scanned image
#             image = cv2.imread(image_path)
#             h, w, _ = image.shape
#             image = image[:h // 2, :w // 2]
#             cv2.imwrite(image_path, image)

#             # Doing now the actual scanning
#             scan = subprocess.run(f'python3 HTR/ocr.py {image_path}', shell=True)
#             if scan.returncode == 0:
#                 return JsonResponse({'status': 'success', 'message': 'Scanning complete'})
#             else:
#                 return JsonResponse({'status': 'error', 'message': 'Scanning failed'})

#     return JsonResponse({'status': 'complete', 'message': 'Scanning complete'})






@csrf_exempt
def scan_paper(request):
    # Windows-specific image path using backslashes
    if platform.system() == "Windows":
        image_path = r'HTR\scannedImages\scanned_form.png'
    else:
        image_path = 'HTR/scannedImages/scanned_form.png'  # Default for Linux/macOS
    
    # Determine the operating system
    system_platform = platform.system()

    # If it's a Linux system, use scanimage
    if system_platform == "Linux":
        with open(image_path, 'wb') as f:
            is_scan = subprocess.run('scanimage --format=png --mode Color --resolution 600', stdout=f, shell=True)
            if is_scan.returncode != 0:
                # Cropping the scanned image if scan failed
                image = cv2.imread(image_path)
                h, w, _ = image.shape
                image = image[:h // 2, :w // 2]
                cv2.imwrite(image_path, image)

                # Perform OCR (this is assuming 'ocr.py' is the process for OCR)
                scan = subprocess.run(f'python3 HTR/ocr.py {image_path}', shell=True)
                if scan.returncode == 0:
                    return JsonResponse({'status': 'success', 'message': 'Scanning complete'})
                else:
                    return JsonResponse({'status': 'error', 'message': 'Scanning failed'})
    
    # If it's a Windows system, use WIA
    elif system_platform == "Windows":
        try:
            # Initialize COM library
            pythoncom.CoInitialize() 

            # Initialize WIA
            wia = win32com.client.Dispatch("WIA.CommonDialog")
            device_manager = win32com.client.Dispatch("WIA.DeviceManager")

            # List connected devices
            print("Connected devices:")
            for device in device_manager.DeviceInfos:
                print(f"ID: {device.DeviceID}, Name: {device.Properties['Name'].Value}")

            # Select a scanner
            print("\nSelect a scanner:")
            device = wia.ShowSelectDevice(1, False)  # 1 = Scanner, 0 = Camera

            if device:
                print(f"Selected device: {device.Properties['Name'].Value}")
                print('po')


                 # Check the number of items in the device
                item_count = len(device.Items)
                print(f"Number of items in the device: {item_count}")

                if item_count > 0:
                    # Scan the first item
                    item = device.Items[0]
                    item.Properties["6147"].Value = 600  # Horizontal Resolution (DPI)
                    item.Properties["6148"].Value = 600  # Vertical Resolution (DPI)
                    item.Properties["6146"].Value = 1    # Color Intent (1 = Color, 2 = Grayscale, 4 = Black-White)
                   
                    image_file = wia.ShowTransfer(item, "{B96B3CAB-0728-11D3-9D7B-0000F81EF32E}")  # FormatID for PNG
                    if os.path.exists(image_path):
                        os.remove(image_path)
                    image_file.SaveFile(image_path)
                    print("Image scanned and saved.")

                    # Cropping the scanned image
                    image = cv2.imread(image_path)
                    if image is None:
                        return JsonResponse({'status': 'error', 'message': 'Failed to read scanned image'})

                    h, w, _ = image.shape
                    cropped_image = image[:h // 2, :w // 2]
                    cv2.imwrite(image_path, cropped_image)

                    # Perform OCR on the cropped image
                    scan = subprocess.run(f'python HTR/ocr_windows.py {image_path}', shell=True)
                    if scan.returncode == 0:
                        return JsonResponse({'status': 'success', 'message': 'Scanning complete'})
                    else:
                        return JsonResponse({'status': 'error', 'message': 'OCR failed'})

            return JsonResponse({'status': 'error', 'message': 'No items found in the device'})

        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})

        finally:
            pythoncom.CoUninitialize()  # Uninitialize COM library

        return JsonResponse({'status': 'complete', 'message': 'Scanning complete'})
    # # Return a message for unsupported platforms
    # else:
    #     return JsonResponse({'status': 'error', 'message': 'Unsupported OS for scanning'})

    # return JsonResponse({'status': 'complete', 'message': 'Scanning complete'})



def read_txt_file(file_path):
    try:
        with open(file_path, 'r') as file:
            lines = file.readlines() 
        return [line.strip() for line in lines]
    except FileNotFoundError:
        print("Pota ka wara didi")
        return None


def borrower_form_view(request):
    if request.method == 'GET' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        data = get_borrower_data()  # Existing function
        return JsonResponse(data)  # Return data as JSON

    # Default behavior if accessed directly
    data = get_borrower_data()
    forms = BorrowItemForm(initial=data)
    return render(request, 'home.html', context={"form": forms})



def get_borrower_data():
    file_path = "HTR/data/data.txt"
    txt_data = read_txt_file(file_path)
    print(txt_data)

    if txt_data:
        last_name = txt_data[0].title()
        first_name = txt_data[1].title()
        middle_name = txt_data[2].title()
        item_name = txt_data[3].title()
        if item_name is None:
            item_name = ''
        item_quantity =int(txt_data[4])
        if item_quantity is None:
            item_quantity = 0
        
        # Fetch the available quantity from the inventory
        inventory_item = get_object_or_404(InventoryItem, name=item_name)
        available_quantity = inventory_item.quantity

        # Validate the item_quantity
        if item_quantity > available_quantity:
            item_quantity = available_quantity

        borrower_data = {
            'borrower_last_name': last_name,
            'borrower_first_name': first_name,
            'borrower_middle_name': middle_name,
            'item_name': item_name,
            'item_quantity': item_quantity,
            'date_borrowed': txt_data[5] if len(txt_data) > 5 else '',
        }
    else:
        borrower_data = {
            'borrower_last_name': '',
            'borrower_first_name': '',
            'borrower_middle_name': '',
            'item_name': '',
            'item_quantity': 0,
            'date_borrowed': '',
        }

    return borrower_data


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def borrow_item_api(request):
    """
    API endpoint for borrowing items
    """
    serializer = BorrowedItemSerializer(data=request.data)
    if serializer.is_valid():
        item_name = serializer.validated_data['item_name']
        item_quantity = serializer.validated_data['item_quantity']
        
        try:
            inventory_item = InventoryItem.objects.get(item_name=item_name)
            available_quantity = inventory_item.available_quantity()
            
            if item_quantity > available_quantity:
                return Response(
                    {"error": f"Only {available_quantity} item(s) available for borrowing."},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
            borrowed_item = serializer.save(
                borrower_name=request.user.username,
                status='borrowed'
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
            
        except InventoryItem.DoesNotExist:
            return Response(
                {"error": "Item not found in inventory."},
                status=status.HTTP_404_NOT_FOUND
            )
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def return_item_api(request, item_id):
    """
    API endpoint for returning items
    """
    try:
        item = BorrowedItem.objects.get(id=item_id, borrower_name=request.user.username)
        if item.status == 'returned':
            return Response(
                {"error": "Item has already been returned."},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        item.status = 'returned'
        item.return_date = timezone.now()
        item.save()
        
        serializer = BorrowedItemSerializer(item)
        return Response(serializer.data)
        
    except BorrowedItem.DoesNotExist:
        return Response(
            {"error": "Borrowed item not found."},
            status=status.HTTP_404_NOT_FOUND
        )

class InventoryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for viewing inventory items
    """
    queryset = InventoryItem.objects.all()
    serializer_class = InventoryItemSerializer
    permission_classes = [IsAuthenticated]

class BorrowedItemViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for viewing borrowed items
    """
    serializer_class = BorrowedItemSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return BorrowedItem.objects.filter(borrower_name=self.request.user.username)


def scan_form(request):
    if request.method == 'GET':
        return render(request, 'scan.html')

def upload_photo(request):
    if request.method == 'POST' and request.FILES.get('photo'):
        photo = request.FILES['photo']
        fs = FileSystemStorage()
        # Define a fixed filename
        filename = "photo.jpg"
        file_path = os.path.join(fs.location, filename)

        # Check if the file already exists and delete it
        if os.path.exists(file_path):
            os.remove(file_path)

        # Save the new photo with the same name
        fs.save(filename, photo)
        file_url = fs.url(filename)
        return JsonResponse({'file_url': file_url})
    
    return JsonResponse({'error': 'No photo uploaded'}, status=400)




from django.shortcuts import render
from django.http import JsonResponse
import base64
from django.core.files.base import ContentFile
from django.conf import settings
import os

def capture_image(request):
    if request.method == 'POST':
        image_data = request.POST.get('image_data')
        if image_data:
            # Decode base64 image
            format, imgstr = image_data.split(';base64,')
            ext = format.split('/')[-1]
            image = ContentFile(base64.b64decode(imgstr), name=f"captured_image.{ext}")

            # Save the image locally
            image_path = os.path.join(settings.MEDIA_ROOT, image.name)
            with open(image_path, 'wb') as f:
                f.write(image.read())

            return JsonResponse({'message': 'Image uploaded successfully', 'image_url': f"{settings.MEDIA_URL}{image.name}"})
        return JsonResponse({'error': 'No image data provided'}, status=400)

    return render(request, 'scan2.html')

