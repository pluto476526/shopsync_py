from django.urls import path
from shop import views



urlpatterns = [
        path('<str:name>/', views.index, name='shop'),
        path('<str:name>/products/', views.products_view, name='products'),
        path('<str:name>/dashboard/', views.shop_dash_view, name='shop_dash'),
        path('<str:name>/details/<str:pk>/', views.product_details_view, name='product_details'),
        path('<str:name>/cart/', views.cart_view, name='cart'),
        path('<str:name>/checkout/', views.checkout_view, name='checkout'),
        path('<str:name>/history/', views.history_view, name='history'),
        path('<str:name>/orders/<str:order_id>/', views.order_details_view, name='order_details'),
        path('<str:name>/categories/', views.categories_view, name='categories'),
        path('<str:name>/add_to_cart/<str:product_id>/', views.add_to_cart_view, name='add_to_cart_view'),
        path('<str:name>/clear_cart/', views.clear_cart_view, name='clear_cart'),
        path('<str:name>/wishlist/', views.wishlist_view, name='wishlist'),
        path('<str:name>/add_to_wishlist/<str:product_id>/', views.add_to_wishlist_view, name='add_to_wishlist_view'),
        path('<str:name>/contact_us/', views.helpdesk_view, name='shop_helpdesk'),
        path('<str:name>/about/', views.about_view, name='shop_about'),
        path('<str:name>/<str:model_name>/<int:object_id>/delete/', views.delete_view, name='shop_delete'),
        path('<str:name>/addresses/', views.my_addresses_view, name='shop_addresses'),
        path('<str:name>/return_items/<str:order_id>', views.returns_view, name='returns_page'),
        path('<str:name>/returns and cancellations', views.returns_and_cancellations_view, name='returns_and_cancellations'),
]




