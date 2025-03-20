from django.contrib import admin
from dash.models import (
    Profile,
    Category,
    Inventory,
    Supplier,
    Delivery,
    DeliveryItem,
    PaymentMethod,
    TodaysDeal,
    Units,
    LowStockThreshold,
)


admin.site.register(Profile)
admin.site.register(Category)
admin.site.register(Inventory)
admin.site.register(Supplier)
admin.site.register(Delivery)
admin.site.register(DeliveryItem)
admin.site.register(PaymentMethod)
admin.site.register(TodaysDeal)
admin.site.register(Units)
admin.site.register(LowStockThreshold)
