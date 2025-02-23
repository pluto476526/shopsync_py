from django.db import models
import secrets
import string


class Role(models.Model):
    shop = models.ForeignKey('shop.Shop', on_delete=models.CASCADE)
    role_name = models.CharField(max_length=20)
    is_deleted = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.shop}: {self.role_name}'


class Profile(models.Model):
    user = models.OneToOneField('auth.User', on_delete=models.CASCADE, related_name='profile')
    identifier = models.CharField(max_length=10, unique=True, null=True)
    avatar = models.ImageField(default='user.jpg')
    shop = models.ForeignKey('shop.Shop', on_delete=models.SET_NULL, blank=True, null=True)
    in_staff = models.BooleanField(default=False)
    role = models.ForeignKey(Role, on_delete=models.SET_NULL, blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    is_deleted = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username}'s profile"

    def save(self, *args, **kwargs):
        if not self.identifier:
            self.identifier = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(8))
        super().save(*args, **kwargs)


class Supplier(models.Model):
    shop = models.ForeignKey('shop.Shop', on_delete=models.CASCADE)
    name = models.CharField(max_length=50)
    is_deleted = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.shop}: {self.name}'
    

class Category(models.Model):
    shop = models.ForeignKey('shop.Shop', on_delete=models.CASCADE)
    category = models.CharField(max_length=50)
    description = models.TextField(blank=True, null=True)
    is_featured = models.BooleanField(default=False)
    avatar = models.ImageField(default='dp1.jpg')
    in_sale = models.BooleanField(default=False)
    percent_off = models.PositiveIntegerField(default=0)
    timestamp = models.DateTimeField(auto_now_add=True)
    total_sales = models.PositiveIntegerField(default=0)
    is_deleted = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.shop}: {self.category}'


class Units(models.Model):
    shop = models.ForeignKey('shop.Shop', on_delete=models.CASCADE)
    units = models.CharField(max_length=20)
    is_deleted = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.shop}: {self.units}'


class LowStockThreshold(models.Model):
    shop = models.ForeignKey('shop.Shop', on_delete=models.CASCADE)
    threshold = models.PositiveIntegerField(default=0)
    is_deleted = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.shop}: {self.threshold}'


class Inventory(models.Model):
    shop = models.ForeignKey('shop.Shop', on_delete=models.CASCADE)
    avatar1 = models.ImageField(default='pd1.jpg')
    avatar2 = models.ImageField(default='pd2.jpg')
    avatar3 = models.ImageField(default='pd3.jpg')
    avatar4 = models.ImageField(default='pd4.jpg')
    avatar5 = models.ImageField(default='pd5.jpg')
    product = models.CharField(max_length=50)
    product_id = models.CharField(max_length=10, unique=True)
    category = models.ForeignKey('dash.Category', on_delete=models.SET_NULL, null=True)
    description = models.CharField(max_length=250, blank=True, null=True)
    price = models.PositiveIntegerField(default=0)
    units = models.ForeignKey('dash.Units', on_delete=models.SET_NULL, null=True)
    quantity = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=20, default='available') # available
    is_featured = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)
    in_deals = models.BooleanField(default=False)
    in_discount = models.BooleanField(default=False)
    in_sale = models.BooleanField(default=False)
    discount = models.PositiveIntegerField(default=0)
    percent_off = models.PositiveIntegerField(default=0)
    # options = 
    supplier = models.ForeignKey('dash.Supplier', on_delete=models.SET_NULL, blank=True, null=True)
    available = models.BooleanField(default=False)
    order_amount = models.PositiveIntegerField(default=0)
    order_instructions = models.TextField(blank=True, null=True)
    total_sales = models.PositiveIntegerField(default=0)
    in_orders = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.shop}: {self.product}'

    def save(self, *args, **kwargs):
        if not self.product_id:
            self.product_id = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(8))
        super().save(*args, **kwargs)


class Review(models.Model):
    user = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True)
    email = models.EmailField(blank=True, null=True)
    productID = models.ForeignKey('dash.Inventory', on_delete=models.CASCADE)
    comment = models.CharField(max_length=100)
    body = models.TextField(blank=True, null=True)
    rating = models.PositiveIntegerField(default=0)
    timestamp = models.DateTimeField(auto_now_add=True)
    is_deleted = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.productID}: {self.comment}'


class PaymentMethod(models.Model):
    shop = models.ForeignKey('shop.Shop', on_delete=models.CASCADE)
    method = models.CharField(max_length=20)
    is_deleted = models.BooleanField(default=False)
    
    def __str__(self):
        return f'{self.shop}: {self.method}'



class Delivery(models.Model):
    shop = models.ForeignKey('shop.Shop', on_delete=models.CASCADE)
    username = models.ForeignKey('auth.User', on_delete=models.SET_NULL, blank=True, null=True, related_name='customer')
    unregistered_user = models.CharField(max_length=50, blank=True, null=True)
    order_number = models.CharField(max_length=10, blank=True, null=True)
    avatar = models.ImageField(default='shop1.jpg')
    timestamp = models.DateTimeField(auto_now_add=True)
    time_confirmed = models.DateTimeField(blank=True, null=True)
    time_shipped = models.DateTimeField(blank=True, null=True)
    time_completed = models.DateTimeField(blank=True, null=True)
    phone = models.CharField(max_length=15, blank=True, null=True)
    email = models.EmailField(unique=False, blank=True, null=True)
    town = models.CharField(max_length=20, null=True, blank=True)
    address = models.ForeignKey('shop.Address', on_delete=models.SET_NULL, blank=True, null=True)
    payment_method = models.ForeignKey('dash.PaymentMethod', on_delete=models.SET_NULL, blank=True, null=True)
    admin = models.ForeignKey('auth.User', on_delete=models.SET_NULL, blank=True, null=True, related_name='admin')
    driver = models.ForeignKey('dash.Profile', on_delete=models.SET_NULL, blank=True, null=True, related_name='staff')
    note = models.TextField(blank=True, null=True)
    source = models.CharField(max_length=10, default='dash') # dash, cart
    is_deleted = models.BooleanField(default=False)
    status = models.CharField(max_length=20, default='processing') # processing, confirmed, shipped, completed
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return f"{self.username}'s delivery"
    
    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(10))
        super().save(*args, **kwargs)

class DeliveryItem(models.Model):
    delivery = models.ForeignKey('dash.Delivery', on_delete=models.CASCADE, related_name='items', null=True)
    product = models.ForeignKey('dash.Inventory', on_delete=models.SET_NULL, null=True)
    quantity = models.PositiveIntegerField()
    total = models.DecimalField(max_digits=10, decimal_places=2)

    def save(self, *args, **kwargs):
        """Automatically calculate the total price of the item"""
        if self.product:
            self.total = self.product.price * self.quantity
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.product} x {self.quantity} (Total: {self.total})'

class Coupon(models.Model):
    shop = models.ForeignKey('shop.Shop', on_delete=models.CASCADE)
    percent_off = models.PositiveIntegerField()
    coupon_id = models.CharField(max_length=11, unique=True)
    status = models.CharField(max_length=10, default='active') # active, inactive
    timestamp = models.DateTimeField(auto_now_add=True)
    total_sales = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.shop}: {self.percent_off}'

    def save(self, *args, **kwargs):
        if not self.coupon_id:
            self.coupon_id = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(10))
        super().save(*args, **kwargs)


class TodaysDeal(models.Model):
    shop = models.ForeignKey('shop.Shop', on_delete=models.CASCADE)
    product_id = models.CharField(max_length=10)
    product = models.CharField(max_length=50, null=True)
    avatar = models.ImageField(default='dp1.jpg')
    category = models.CharField(max_length=20, null=True)
    price = models.PositiveIntegerField(default=0)
    discount = models.PositiveIntegerField(default=0)
    time = models.DateTimeField(null=True)
    status = models.CharField(max_length=10, default='active') # active, inactive
    timestamp = models.DateTimeField(auto_now_add=True)
    total_sales = models.PositiveIntegerField(default=0)
    is_deleted = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.shop}: {self.product_id}'
