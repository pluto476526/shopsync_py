from django.urls import path
from shop import views



urlpatterns = [
        path('<str:name>/', views.index, name='shop'),
        path('<str:name>/products/', views.products_view, name='products'),
        path('<str:name>/products/<str:category>/', views.products_view2, name='products2'),
        path('<str:name>/details/<str:pk>/', views.product_details_view, name='product_details'),
        path('<str:name>/cart/', views.cart_view, name='cart'),
        path('<str:name>/checkout/', views.checkout_view, name='checkout'),
        path('<str:name>/history/', views.history_view, name='history'),
        path('<str:name>/orders/<str:order_id>/', views.order_details_view, name='order_details'),
        path('<str:name>/categories/', views.categories_view, name='categories'),
        path('<str:name>/add_to_cart/<str:product_no>/', views.add_to_cart, name='add_to_cart'),
        path('<str:name>/wishlist/', views.wishlist_view, name='wishlist'),
        path('<str:name>/wishes/<str:product_no>/', views.add_to_wishlist, name='wishes'),
        path('<str:name>/helpdesk/', views.helpdesk_view, name='shop_helpdesk'),
        path('<str:name>/about/', views.about_view, name='about'),
]




