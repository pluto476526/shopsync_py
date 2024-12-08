from django.shortcuts import render, redirect, get_object_or_404
from django.db import models, connection
from django.contrib import messages
from django.contrib.auth.models import User
from shop.models import Shop, Cart
from dash.models import Inventory, Category, PaymentMethod, Delivery, HelpDesk
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


def add_to_cart(request, name, product_no):
    if request.method == 'GET':
        the_shop = get_shop(name)
        product = get_object_or_404(Inventory, product_id=product_no)
        category = get_object_or_404(Category, shop=the_shop, category=product.category.category)
        Cart.objects.create(
            shop = the_shop,
            customer = request.user,
            category = category,
            product = product,
            cart_product_id = product.product_id,
            avatar = product.avatar,
            description = product.description,
            price = product.price,
            units = product.units,
            quantity = 1,
            total = product.price,
        )
        messages.success(request, f'{product.product} added to cart')
        return redirect('shop', the_shop)
    return {}


def add_to_wishlist(request, name, product_no):
    the_shop = get_shop(name)
    wishes = Cart.objects.filter(shop=the_shop, customer=request.user, status='in_wishes')

    if request.method == 'GET':
        for wish in wishes:
            if product_no == wish.cart_product_id:
                messages.info(request, 'Item already in wishlist')
                return redirect('shop', the_shop.name)
    
        product = get_object_or_404(Inventory, product_id=product_no)
        category = get_object_or_404(Category, shop=the_shop, category=product.category.category)
        Cart.objects.create(
            shop = the_shop,
            customer = request.user,
            category = category,
            product = product,
            cart_product_id = product.product_id,
            avatar = product.avatar,
            description = product.description,
            price = product.price,
            units = product.units,
            quantity = 1,
            total = product.price,
            status = 'in_wishes',
        )
        messages.success(request, f'{product.product} added to wishlist')
        return redirect('shop', the_shop.name)
    return {}


def index(request, name):
    the_shop = get_shop(name)
    categories = Category.objects.filter(shop=the_shop)
    other_categories = categories.filter(is_featured=False)[:3]
    featured_categories = categories.filter(is_featured=True)[:3]
    featured_products = Inventory.objects.filter(shop=the_shop, is_featured=True)
    cart_products = Cart.objects.filter(shop=the_shop, customer=request.user, status='pending').values_list('cart_product_id', flat=True)
    featured_products = featured_products.exclude(product_id__in=cart_products)[:8]
    context = {
        'the_shop': the_shop,
        'categories': other_categories,
        'featured_categories': featured_categories,
        'featured_products': featured_products,
    }
    return render(request, 'shop/index.html', context)


def products_view(request, name):
    the_shop = get_shop(name)
    products = Inventory.objects.filter(shop=the_shop, status='available')
    cart_products = Cart.objects.filter(shop=the_shop, customer=request.user, status='pending').values_list('cart_product_id', flat=True)
    products = products.exclude(product_id__in=cart_products)
    categories = Category.objects.filter(shop=the_shop)
    context = {
        'the_shop': the_shop,
        'products': products,
        'categories': categories,
    }
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
    in_cart = Cart.objects.filter(shop=the_shop, customer=request.user, status='pending').values_list('cart_product_id', flat=True)

    try:
        other_products = Inventory.objects.filter(shop=the_shop, category=category).exclude(id=product.id)
        other_products = other_products.exclude(product_id__in=in_cart)

    except Exception as e:
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


def categories_view(request, name):
    the_shop = get_shop(name)
    categories = Category.objects.filter(shop=the_shop)
    context = {
        'the_shop': the_shop,
        'categories': categories,
    }
    return render(request, 'shop/categories.html', context)


def products_view2(request, name, category):
    the_shop = get_shop(name)
    category_instance = get_object_or_404(Category, shop=the_shop, category=category)
    products = Inventory.objects.filter(shop=the_shop, category=category_instance, status='available')
    context = {
        'products': products,
        'the_shop': the_shop,
    }
    return render(request, 'shop/products.html', context)


def wishlist_view(request, name):
    the_shop = get_shop(name)
    wishes = Cart.objects.filter(shop=the_shop, customer=request.user, status='in_wishes')

    if request.method == 'POST':
        products_to_update = []

        for product in wishes:
            product.status = 'pending'
            products_to_update.append(product)

        Cart.objects.bulk_update(products_to_update, ['status'])
        messages.success(request, 'Wishlist added to cart')
        return redirect('wishlist', the_shop.name)

    context = {
        'the_shop': the_shop,
        'wishes': wishes,
    }
    return render(request, 'shop/wishlist.html', context)


def helpdesk_view(request, name):
    the_shop = get_shop(name)
    
    if request.method == 'POST':
        phone = request.POST.get('phone')
        email = request.POST.get('email')
        issue = request.POST.get('issue')
        description = request.POST.get('description')
        source = request.POST.get('source')

        if source == 'send_issue':
            HelpDesk.objects.create(
                shop = the_shop,
                username = request.user,
                phone = phone,
                email = email,
                issue = issue,
                description = description,
            )
            messages.success(request, 'Message sent. You have received a help ID.')
            return redirect('shop_helpdesk', the_shop.name)

    issues = HelpDesk.objects.filter(username=request.user)
    context = {
        'the_shop': the_shop,
        'issues': issues,
    }
    return render(request, 'shop/helpdesk.html', context)



