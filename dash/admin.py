from django.contrib import admin
from dash.models import Profile, Category, Inventory, Supplier, Delivery, ShopStaff, PaymentMethod

# Register your models here.

admin.site.register(Profile)
admin.site.register(Category)
admin.site.register(Inventory)
admin.site.register(Supplier)
admin.site.register(Delivery)
admin.site.register(ShopStaff)
admin.site.register(PaymentMethod)

