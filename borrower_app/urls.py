from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('', views.home, name='home'),
    path('data_table/', views.data_table_view, name='data_table'),
    path('inventory/', views.inventory_view, name='inventory'),
    path('inventory/edit/<int:item_id>/', views.edit_inventory_item, name='edit_inventory_item'),
    path('inventory/delete/<int:item_id>/', views.delete_inventory_item, name='delete_inventory_item'),
    path('return_item/<int:item_id>/', views.return_item, name='return_item'),
    path('delete_item/<int:item_id>/', views.delete_item, name='delete_item'),
    path('get_item_names/', views.get_item_names, name='get_item_names'),  # new URL for item names

]
