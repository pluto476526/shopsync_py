from django.urls import path
from dash import views



urlpatterns = [
    path('', views.index, name='dash'),
    path('categories/', views.categories, name='categories'),
    path('inventory/', views.inventory_view, name='inventory'),
    path('orders/', views.orders_view, name='orders'),
    path('deliveries/', views.deliveries_view, name='deliveries'),
    path('confirmed_deliveries/', views.confirmed_deliveries_view, name='confirmed_deliveries'),
    path('track_order/', views.track_order_view, name='track_order'),
    path('order/<str:order_id>/', views.order_details_view, name='order_details'),
    path('delete/<int:pk>/', views.delete_view, name='delete'),
    path('sales/online/', views.online_sales_view, name='online_sales'),
    path('sales/physical/', views.physical_sales_view, name='physical_sales'),
    path('helpdesk/', views.user_helpdesk_view, name='helpdesk'),
    path('profile/', views.shop_profile_view, name='shop_profile'),
]



