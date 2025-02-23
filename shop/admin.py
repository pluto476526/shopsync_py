from django.contrib import admin
from shop.models import Shop, ShopCategory, Cart, CartItem, Address


# Register your models here.

admin.site.register(Shop)
admin.site.register(ShopCategory)
admin.site.register(Cart)
admin.site.register(Address)
admin.site.register(CartItem)
