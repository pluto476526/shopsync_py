from django.urls import path
from shop import views



urlpatterns = [
        path('<str:name>/', views.index, name='shop'),
        path('<str:name>/products/', views.products_view, name='products'),
        path('<str:name>/details/<str:pk>/', views.product_details_view, name='product_details'),
        path('<str:name>/cart/', views.cart_view, name='cart'),
        path('<str:name>/checkout/', views.checkout_view, name='checkout'),
        path('<str:name>/history/', views.history_view, name='history'),
        path('<str:name>/orders/<str:order_id>/', views.order_details_view, name='order_details'),
]




