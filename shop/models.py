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
    name = models.CharField(max_length=50, unique=True)
    shopID = models.CharField(max_length=10, unique=True, null=True)
    bio = models.TextField(blank=True, null=True)
    logo = models.ImageField(default='logo.jpg')
    dp1 = models.ImageField(default='dp1.jpg')
    dp2 = models.ImageField(default='dp2.jpg')
    dp3 = models.ImageField(default='dp3.jpg')
    title1 = models.CharField(max_length=50, default='Find Top Brands.')
    title2 = models.CharField(max_length=50, default='Exceptional Quality.')
    title3 = models.CharField(max_length=50, default='Shop With Ease')
    shop_category = models.ForeignKey('shop.ShopCategory', on_delete=models.SET_NULL, null=True, related_name='shop_category')
    location = models.CharField(max_length=20, blank=True, null=True)
    address = models.CharField(max_length=100, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=15, blank=True, null=True)
    instagram = models.CharField(max_length=50, blank=True, null=True)
    twitter = models.CharField(max_length=50, blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    is_featured = models.BooleanField(default=False)
    is_banned = models.BooleanField(default=False)
    status = models.CharField(max_length=20, default='pending')
    total_sales = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.shopID:
            self.shopID = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(8))
        super().save(*args, **kwargs)


class Cart(models.Model):
    shop = models.ForeignKey('shop.Shop', on_delete=models.CASCADE)
    customer = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    cart_product_id = models.CharField(max_length=10)
    category = models.CharField(max_length=50)
    product = models.ForeignKey('dash.Inventory', on_delete=models.CASCADE)
    avatar = models.ImageField(default='dp1.jpg')
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


class ShopHelpDesk(models.Model):
    shop = models.ForeignKey('shop.Shop', on_delete=models.SET_NULL, null=True, related_name='shop')
    username = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, related_name='shopper')
    phone = models.CharField(max_length=15, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    issue = models.CharField(max_length=100)
    description = models.TextField()
    help_id = models.CharField(max_length=10, unique=True, blank=True, null=True)
    status = models.CharField(max_length=10, default='pending')
    admin = models.ForeignKey('auth.User', on_delete=models.SET_NULL, blank=True, null=True, related_name='cc')
    is_sorted = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.shop}: {self.issue}'

    def save(self, *args, **kwargs):
        if not self.help_id:
            self.help_id = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(8))
        super().save(*args, **kwargs)

