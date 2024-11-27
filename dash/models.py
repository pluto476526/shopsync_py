from django.db import models
from django.contrib.auth.models import User
from shop.models import Shop
import secrets
import string


# Create your models here

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')

    def __str__(self):
        return f"{self.user.username}'s profile"


class ShopStaff(models.Model):
    shop = models.ForeignKey('shop.Shop', on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    job = models.CharField(max_length=100)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.shop}: {self.name}'


class Supplier(models.Model):
    shop = models.ForeignKey('shop.Shop', on_delete=models.CASCADE)
    name = models.CharField(max_length=50)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.shop}: {self.name}'
    

class Category(models.Model):
    shop = models.ForeignKey('shop.Shop', on_delete=models.CASCADE)
    category = models.CharField(max_length=50)
    description = models.TextField(blank=True, null=True)
    is_featured = models.BooleanField(default=False)
    avatar = models.ImageField(default='avatar5.png')
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.shop}: {self.category}'


class Inventory(models.Model):
    shop = models.ForeignKey('shop.Shop', on_delete=models.CASCADE)
    avatar = models.ImageField(default='avatar5.png')
    product = models.CharField(max_length=50)
    product_id = models.CharField(max_length=10, unique=True)
    category = models.ForeignKey('dash.Category', on_delete=models.SET_NULL, null=True)
    description = models.CharField(max_length=250, blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    units = models.CharField(max_length=10, blank=True, null=True)
    quantity = models.PositiveIntegerField()
    status = models.CharField(max_length=20, default='available')
    is_featured = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)
    in_deals = models.BooleanField(default=False)
    discount = models.IntegerField(default=0)
    # options = 
    supplier = models.ForeignKey('dash.Supplier', on_delete=models.SET_NULL, blank=True, null=True)

    def __str__(self):
        return f'{self.shop}: {self.product}'

    def save(self, *args, **kwargs):
        if not self.product_id:
            self.product_id = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(8))
        super().save(*args, **kwargs)


class PaymentMethod(models.Model):
    shop = models.ForeignKey('shop.Shop', on_delete=models.CASCADE, null=True)
    payment_method = models.CharField(max_length=20)
    
    def __str__(self):
        return self.payment_method


class Delivery(models.Model):
    shop = models.ForeignKey('shop.Shop', on_delete=models.CASCADE)
    username = models.ForeignKey('auth.User', on_delete=models.SET_NULL, blank=True, null=True, related_name='customer')
    unregistered_user = models.CharField(max_length=50, blank=True, null=True)
    order_number = models.CharField(max_length=10)
    category = models.ForeignKey('dash.Category', on_delete=models.SET_NULL, null=True)
    product = models.ForeignKey('dash.Inventory', on_delete=models.SET_NULL, null=True)
    avatar = models.ImageField(default='avatar5.png')
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    units = models.CharField(max_length=20)
    discount = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=20, default='processing')
    admin = models.ForeignKey('auth.User', on_delete=models.SET_NULL, blank=True, null=True, related_name='admin')
    driver = models.ForeignKey('dash.ShopStaff', on_delete=models.SET_NULL, blank=True, null=True, related_name='staff')
    timestamp = models.DateTimeField(auto_now_add=True)
    time_confirmed = models.DateTimeField(blank=True, null=True)
    time_in_transit = models.DateTimeField(blank=True, null=True)
    time_completed = models.DateTimeField(blank=True, null=True)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    phone = models.CharField(max_length=15, blank=True, null=True)
    email = models.EmailField(unique=False, blank=True, null=True)
    county = models.CharField(max_length=20, default='Nairobi')
    town = models.CharField(max_length=20, default='Nairobi')
    address = models.CharField(max_length=100, blank=True, null=True)
    payment_method = models.ForeignKey('dash.PaymentMethod', on_delete=models.SET_NULL, blank=True, null=True)
    instructions = models.TextField(blank=True, null=True)
    source = models.CharField(max_length=10, default='dash')

    def __str__(self):
        return f'{self.shop}: {self.order_number}'


    def save(self, *args, **kwargs):
        if not self.order_number:  
            self.order_number = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(8))
        super().save(*args, **kwargs)








