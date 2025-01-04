# shop/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Sum, Count, F
from django.contrib.auth.decorators import login_required
from shop.models import Shop, Cart, ShopHelpDesk
from dash.models import Inventory, Category, PaymentMethod, Delivery, TodaysDeal, Profile
from datetime import datetime
import logging
import secrets
import string


# Logger setup
logger = logging.getLogger(__name__)

# Helper function: Generate a random order number
def random_id():
    return ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(8))

# Helper function: Retrieve a shop by name
def get_shop(name):
    return get_object_or_404(Shop, name=name)

# Helper function: Calculate cart total
def calculate_cart_total(cart_items):
    return cart_items.aggregate(total=Sum('total'))['total'] or 0

# View: Add product to cart
def add_to_cart(request, name, product_no):
    the_shop = get_shop(name)
    product = get_object_or_404(Inventory, product_id=product_no, shop=the_shop)

    # Check if product is already in cart
    if Cart.objects.filter(shop=the_shop, customer=request.user, cart_product_id=product.product_id, status='pending').exists():
        messages.info(request, f"{product.product} is already in your cart.")
        return redirect('products_view', name=the_shop.name)

    # Add to cart
    Cart.objects.create(
        shop=the_shop,
        customer=request.user,
        product=product,
        cart_product_id=product.product_id,
        avatar=product.avatar,
        description=product.description,
        price=product.price,
        units=product.units,
        quantity=1,
        total=product.price,
    )
    messages.success(request, f"{product.product} added to cart.")
    logger.debug(f"Product {product.product} added to cart by user {request.user}.")
    return redirect('products_view', name=the_shop.name)

# View: Add product to wishlist
def add_to_wishlist(request, name, product_no):
    the_shop = get_shop(name)
    product = get_object_or_404(Inventory, product_id=product_no, shop=the_shop)

    # Check if product is already in wishlist
    if Cart.objects.filter(shop=the_shop, customer=request.user, cart_product_id=product.product_id, status='in_wishes').exists():
        messages.info(request, f"{product.product} is already in your wishlist.")
        return redirect('products_view', name=the_shop.name)

    # Add to wishlist
    Cart.objects.create(
        shop=the_shop,
        customer=request.user,
        product=product,
        cart_product_id=product.product_id,
        avatar=product.avatar,
        description=product.description,
        price=product.price,
        units=product.units,
        quantity=1,
        total=product.price,
        status='in_wishes',
    )
    messages.success(request, f"{product.product} added to wishlist.")
    return redirect('products_view', name=the_shop.name)

# View: Shop homepage
def index(request, name):
    try:
        # Retrieve the shop and user profile
        shop = get_shop(name)
        profile = get_object_or_404(Profile, user=request.user)

        # Fetch categories
        categories = Category.objects.filter(shop=shop)
        top_categories = categories.order_by('-total_sales')[:4]
        f_categories = categories.filter(is_featured=True).order_by('-timestamp')[:3]

        # Fetch products from top categories(tc) excluding those in the user's pending cart
        cart_products = Cart.objects.filter(
            shop=shop, customer=request.user, status='pending'
        ).values_list('cart_product_id', flat=True)
        tc_products = []
        for t in top_categories:
            cat = get_object_or_404(Category, category=t.category)
            products = Inventory.objects.filter(
                shop=shop, category=cat
                ).exclude(product_id__in=cart_products)[:3]
            for p in products:
                tc_products.append(p)

        # Get the most recent timed deal
        deal = TodaysDeal.objects.filter(shop=shop).order_by('-time').first()

        # Prepare context for rendering
        context = {
            'profile': profile,
            'top_categories': top_categories,
            'f_categories': f_categories,
            'tc_products': tc_products,
            'deal': deal,
            'shop': shop,
        }
        return render(request, 'shop/index22.html', context)
    
    except Exception as e:
        # Log the error and show a friendly error page
        logger.error(f"An Error occured while rendering the shop '{name}': {e}")
        messages.error(request, "An error occurred while loading the shop. Please try again later.")
        return redirect('home')  # Adjust this to redirect to an appropriate fallback page


# View: Products list
@login_required
def products_view(request, name):
    the_shop = get_shop(name)
    products = Inventory.objects.filter(shop=the_shop, status='available').exclude(
        product_id__in=Cart.objects.filter(shop=the_shop, customer=request.user, status='pending').values_list('cart_product_id', flat=True)
    )
    categories = Category.objects.filter(shop=the_shop)

    context = {
        'the_shop': the_shop,
        'products': products,
        'categories': categories,
    }
    return render(request, 'shop/products.html', context)

# View: Product details
@login_required
def product_details_view(request, name, pk):
    the_shop = get_shop(name)
    product = get_object_or_404(Inventory, product_id=pk, shop=the_shop)

    if request.method == 'POST':
        quantity = int(request.POST.get('quantity', 1))
        Cart.objects.create(
            shop=the_shop,
            customer=request.user,
            product=product,
            cart_product_id=product.product_id,
            quantity=quantity,
            total=quantity * product.price,
        )
        messages.success(request, f"{quantity} {product.units} of {product.product} added to cart.")
        return redirect('product_details_view', name=name, pk=pk)

    other_products = Inventory.objects.filter(shop=the_shop, category=product.category).exclude(product_id=product.product_id)[:4]

    context = {
        'product': product,
        'the_shop': the_shop,
        'other_products': other_products,
    }
    return render(request, 'shop/product_details.html', context)

# View: Cart
@login_required
def cart_view(request, name):
    the_shop = get_shop(name)
    cart_items = Cart.objects.filter(shop=the_shop, customer=request.user, status='pending')

    if request.method == 'POST':
        product_ids = request.POST.getlist('product_id[]')
        quantities = request.POST.getlist('quantity[]')

        # Bulk update cart items
        for product_id, quantity in zip(product_ids, quantities):
            try:
                quantity = max(1, min(int(quantity), 100))
                cart_item = cart_items.get(pk=product_id)
                cart_item.quantity = quantity
                cart_item.total = quantity * cart_item.price
                cart_item.save()
            except (Cart.DoesNotExist, ValueError):
                messages.error(request, "Invalid cart update request.")

        messages.success(request, "Cart updated successfully.")
        return redirect('cart_view', name=the_shop.name)

    total = calculate_cart_total(cart_items)
    return render(request, 'shop/cart.html', context)

# View: Checkout
@login_required
def checkout_view(request, name):
    the_shop = get_shop(name)
    cart_items = Cart.objects.filter(shop=the_shop, customer=request.user, status='pending')

    if not cart_items.exists():
        messages.error(request, "Your cart is empty.")
        return redirect('cart_view', name=the_shop.name)

    if request.method == 'POST':
        phone = request.POST.get('phone')
        email = request.POST.get('email')
        county = request.POST.get('county')
        town = request.POST.get('town')
        address = request.POST.get('address')
        instructions = request.POST.get('instructions')
        payment_method = request.POST.get('payment_method')
        payment_instance = get_object_or_404(PaymentMethod, shop=the_shop, payment_method=payment_method)
        order_number = random_id()

        # Create deliveries
        deliveries = [
            Delivery(
                shop=the_shop,
                username=request.user,
                order_number=order_number,
                product=item.product,
                quantity=item.quantity,
                price=item.price,
                total=item.total,
                phone=phone,
                email=email,
                county=county,
                town=town,
                address=address,
                payment_method=payment_instance,
                instructions=instructions,
                source='cart',
            )
            for item in cart_items
        ]
        Delivery.objects.bulk_create(deliveries)
        cart_items.update(status='checked_out', checked_out=datetime.now())

        messages.success(request, f"Order #{order_number} checked out successfully.")
        return redirect('shop', name=the_shop)

    total = calculate_cart_total(cart_items)
    payment_methods = PaymentMethod.objects.filter(shop=the_shop)
    context = {'the_shop': the_shop, 'total': total, 'payment_methods': payment_methods}
    return render(request, 'shop/checkout.html', context)

# View: Order history
@login_required
def history_view(request, name):
    the_shop = get_shop(name)
    orders = Delivery.objects.filter(shop=the_shop, username=request.user).values(
        'order_number', 'status'
    ).annotate(total=Sum('total'), count=Count('id'))

    context = {'the_shop': the_shop, 'orders': orders}
    return render(request, 'shop/history.html', context)

# View: Order details
@login_required
def order_details_view(request, name, order_id):
    the_shop = get_shop(name)
    orders = Delivery.objects.filter(shop=the_shop, order_number=order_id)
    context = {'the_shop': the_shop, 'orders': orders}
    return render(request, 'shop/order_details.html', context)

# View: Wishlist
@login_required
def wishlist_view(request, name):
    the_shop = get_shop(name)
    wishes = Cart.objects.filter(shop=the_shop, customer=request.user, status='in_wishes')

    if request.method == 'POST':
        wishes.update(status='pending')
        messages.success(request, "Wishlist added to cart.")
        return redirect('wishlist_view', name=the_shop.name)

    context = {'the_shop': the_shop, 'wishes': wishes}
    return render(request, 'shop/wishlist.html', context)

# View: Categories
@login_required
def categories_view(request, name):
    the_shop = get_shop(name)
    categories = Category.objects.filter(shop=the_shop)
    context = {
        'the_shop': the_shop,
        'categories': categories,
    }
    return render(request, 'shop/categories.html', context)

@login_required
def products_view2(request, name, category):
    the_shop = get_shop(name)
    category_instance = get_object_or_404(Category, shop=the_shop, category=category)
    products = Inventory.objects.filter(shop=the_shop, category=category_instance, status='available')
    context = {
        'products': products,
        'the_shop': the_shop,
    }
    return render(request, 'shop/products.html', context)


@login_required
def helpdesk_view(request, name):
    the_shop = get_shop(name)
    
    if request.method == 'POST':
        phone = request.POST.get('phone')
        email = request.POST.get('email')
        issue = request.POST.get('issue')
        description = request.POST.get('description')
        source = request.POST.get('source')

        if source == 'send_issue':
            ShopHelpDesk.objects.create(
                shop = the_shop,
                username = request.user,
                phone = phone,
                email = email,
                issue = issue,
                description = description,
            )
            messages.success(request, 'Message sent. You have received a help ID.')
            return redirect('shop_helpdesk', the_shop.name)

    issues = ShopHelpDesk.objects.filter(username=request.user)
    context = {
        'the_shop': the_shop,
        'issues': issues,
    }
    return render(request, 'shop/helpdesk.html', context)


@login_required
def about_view(request, name):
    the_shop = get_shop(name)
    context = {'the_shop': the_shop}
    return render(request, 'shop/about.html', context)
