from django.shortcuts import render, redirect, get_object_or_404
from django.db import models, connection
from django.contrib import messages
from django.contrib.auth.models import User
from shop.models import Shop, Cart
from dash.models import Inventory, Category, PaymentMethod, Delivery
from datetime import datetime
import logging
import secrets
import string


# Get logger
logger = logging.getLogger(__name__)


# Log queries
def log_queries():
    for query in connection.queries:
        logger.debug(query)


# Generate random id
def random_id():
    return ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(8))


# Get shop
def get_shop(name):
    return get_object_or_404(Shop, name=name)


# Create your views here.

def index(request, name):
    the_shop = get_shop(name)
    context = {'the_shop': the_shop}
    return render(request, 'shop/index.html', context)


def products_view(request, name):
    the_shop = get_shop(name)
    products = Inventory.objects.filter(shop=the_shop, status='available')
    cart_products = Cart.objects.filter(shop=the_shop, customer = request.user, status='pending').values_list('cart_product_id', flat=True)
    products = products.exclude(product_id__in=cart_products)
    context = {'the_shop': the_shop, 'products': products}
    return render(request, 'shop/products.html', context)


def product_details_view(request, name, pk):
    the_shop = get_shop(name)
    product = get_object_or_404(Inventory, product_id=pk)
    category_instance = get_object_or_404(Category, category=product.category.category)

    if request.method == 'POST':
        quantity = request.POST.get('quantity') 
        Cart.objects.create(
            shop = the_shop,
            customer = request.user,
            category = category_instance,
            product = product,
            cart_product_id = product.product_id,
            avatar = product.avatar,
            description = product.description,
            price = product.price,
            units = product.units,
            quantity = quantity,
            total = float(product.price) * float(quantity),
        )
        messages.success(request, f'{quantity} {product.units} of {product.product} added to cart')
        return redirect('products', name=the_shop)

    category = get_object_or_404(Category, category=product.category.category)

    try:
        other_products = Inventory.objects.filter(shop=the_shop, category=category).exclude(id=product.id)

    except Exception as e:
        logger.debug(e)
        other_products = []

    context = {'product': product, 'the_shop': the_shop, 'other_products': other_products}
    return render(request, 'shop/product_details.html', context)


def cart_view(request, name):
    the_shop = get_shop(name)

    if request.method == 'POST':
        product_ids = request.POST.getlist('product_id[]')
        quantities = request.POST.getlist('quantity[]')

        # Prepare bulk update data
        updates = []
        for product_id, quantity in zip(product_ids, quantities):
            try:
                quantity = max(1, min(int(quantity), 100))
                updates.append((product_id, quantity))
            except ValueError:
                messages.error(request, "Invalid quantity provided.")

        # Update all cart items in one query
        for product_id, quantity in updates:
            try:
                Cart.objects.get(pk=product_id).update(quantity=quantity, total=models.F('price') * quantity)

            # Update one product
            except AttributeError:
                cart_item = Cart.objects.get(id=product_id)
                cart_item.quantity = quantity
                cart_item.total = float(cart_item.price) * float(quantity)
                logger.debug(cart_item.total)
                cart_item.save()

        messages.success(request, "Cart updated successfully!")
        return redirect('cart', name=the_shop.name)

    cart = Cart.objects.filter(shop=the_shop, customer=request.user, status='pending')
    cart_total = cart.values('customer').annotate(total_sum=models.Sum('total'))

    if cart_total:
        total_sum = cart_total[0]['total_sum']
        
    else:
        total_sum = 0

    context = {'the_shop': the_shop, 'cart': cart, 'pending_total': total_sum}
    return render(request, 'shop/cart.html', context)


def checkout_view(request, name):
    the_shop = get_shop(name)
    cart = Cart.objects.filter(shop=the_shop, customer=request.user, status='pending')

    if request.method == 'POST':
        phone = request.POST.get('phone')
        email = request.POST.get('email')
        county = request.POST.get('county')
        town = request.POST.get('town')
        address = request.POST.get('address')
        instructions = request.POST.get('instructions')
        payment_method = request.POST.get('payment_method')
        method_instance = get_object_or_404(PaymentMethod, shop=the_shop, payment_method=payment_method)
        order_number = random_id()
        products_to_update = []
        
        for product in cart:
            product_instance = Inventory.objects.get(shop=the_shop, product_id=product.cart_product_id)
            category_instance = Category.objects.get(shop=the_shop, category=product_instance.category.category)
            Delivery.objects.create(
                shop = the_shop,
                username = request.user,
                order_number = order_number,
                category = category_instance,
                product = product_instance,
                avatar = product.avatar,
                quantity = product.quantity,
                price = product.price,
                units = product.units,
                total = product.quantity * product.price,
                phone = phone,
                email = email,
                county = county,
                town = town,
                address = address,
                payment_method = method_instance,
                instructions = instructions,
                source = 'cart',
            )
            product.status = 'checked_out'
            product.checked_out = datetime.now()
            products_to_update.append(product)

        Cart.objects.bulk_update(products_to_update, ['status', 'checked_out'])
        messages.success(request, 'Order checked out')
        return redirect('shop', name=the_shop)

    payment_methods = PaymentMethod.objects.filter(shop=the_shop)
    cart_total = cart.values('customer').annotate(total_sum=models.Sum('total'))

    if cart_total:
        total_sum = cart_total[0]['total_sum']
        
    else:
        total_sum = 0

    context = {'the_shop': the_shop, 'total': total_sum, 'payment_methods': payment_methods}
    return render(request, 'shop/checkout.html', context)


def history_view(request, name):
    the_shop = get_shop(name)
    orders = Delivery.objects.filter(shop=the_shop, username=request.user)
    grouped_orders = orders.values('order_number', 'status').annotate(
        total_amount=models.Sum('total'),
        item_count=models.Count('id')
    )
    context = {'the_shop': the_shop, 'grouped_orders': grouped_orders}
    return render(request, 'shop/history.html', context)


def order_details_view(request, name, order_id):
    the_shop = get_shop(name)
    orders = Delivery.objects.filter(shop=the_shop, order_number=order_id)
    context = {'the_shop': the_shop, 'orders': orders}
    return render(request, 'shop/order_details.html', context)









