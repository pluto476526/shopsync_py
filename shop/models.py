from django.db import models
import secrets
import string


# Create your models here.

class ShopCategory(models.Model):
    category = models.CharField(max_length=30)

    def __str__(self):
        return self.category


class Shop(models.Model):
    owner = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    name = models.CharField(max_length=50)
    bio = models.TextField(blank=True, null=True)
    avatar = models.ImageField(default='shop_profile.jpg')
    image1 = models.ImageField(default='shop_profile1.jpg')
    image2 = models.ImageField(default='shop_profile2.jpg')
    shop_category = models.ForeignKey('shop.ShopCategory', on_delete=models.SET_NULL, null=True, related_name='shop_category')
    timestamp = models.DateTimeField(auto_now_add=True)
    is_featured = models.BooleanField(default=False)

    def __str__(self):
        return self.name


class Cart(models.Model):
    shop = models.ForeignKey('shop.Shop', on_delete=models.CASCADE)
    customer = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    cart_product_id = models.CharField(max_length=10)
    category = models.CharField(max_length=50)
    product = models.ForeignKey('dash.Inventory', on_delete=models.CASCADE)
    avatar = models.ImageField(default='shop_profile.jpg')
    description = models.CharField(max_length=255, blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    units = models.CharField(max_length=20)
    quantity = models.PositiveIntegerField()
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=20, default='pending')
    time_ordered = models.DateTimeField(auto_now_add=True)
    checked_out = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"{self.customer}'s cart: {self.cart_product_id}"


