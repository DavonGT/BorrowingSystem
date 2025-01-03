from django.urls import path, include
from . import views
from rest_framework.routers import DefaultRouter
from django.conf import settings
from django.conf.urls.static import static


router = DefaultRouter()
router.register(r'inventory', views.InventoryViewSet, basename='inventory-api')
router.register(r'borrowed-items', views.BorrowedItemViewSet, basename='borrowed-items-api')

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('home', views.home, name='home'),
    path('data_table/', views.data_table_view, name='data_table'),
    path('inventory/', views.inventory_view, name='inventory'),
    path('inventory/edit/<int:item_id>/', views.edit_inventory_item, name='edit_inventory_item'),
    path('inventory/delete/<int:item_id>/', views.delete_inventory_item, name='delete_inventory_item'),
    path('return_item/<int:item_id>/', views.return_item, name='return_item'),
    path('delete_item/<int:item_id>/', views.delete_item, name='delete_item'),
    path('get_item_names/', views.get_item_names, name='get_item_names'),
    path('scan_paper/', views.scan_paper, name='scan_paper'),
    path('borrower_form_view/', views.borrower_form_view, name='borrower_form_view'),
    
    # API endpoints
    path('api/', include(router.urls)),
    path('api/borrow/', views.borrow_item_api, name='borrow-api'),
    path('api/return/<int:item_id>/', views.return_item_api, name='return-api'),

    # Phone Scanning
    path('scan/', views.scan_form, name='scan_form'),
    path('upload-photo/', views.upload_photo, name='upload_photo'),
    #static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT),
    path('capture-image/', views.capture_image, name='capture_image'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
