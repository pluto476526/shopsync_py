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
]



