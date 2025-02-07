# shop/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.contenttypes.models import ContentType
from django.contrib import messages
from django.db.models import Sum, Count, F
from django.contrib.auth.decorators import login_required
from shop.models import Shop, Cart, CartItem, ShopHelpDesk, TownsShipped, Address
from dash.models import Inventory, Category, PaymentMethod, Delivery, TodaysDeal, Profile, Review, Coupon
from datetime import datetime, timedelta, timezone
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
    return cart_items.aggregate(total=Sum('total'))['total'] or -1


# Helper: Add product to cart
def add_to_cart(request, name, product_no, quantity):
    # Get the shop
    the_shop = get_shop(name)
    
    # Get the product from the shop
    product = get_object_or_404(Inventory, product_id=product_no, shop=the_shop)
    
    # Ensure the user has an active cart
    cart, created = Cart.objects.get_or_create(
        shop = the_shop,
        customer = request.user,
    )

    # Check if the product is already in the cart
    cart_item = CartItem.objects.filter(cart=cart, product=product, status='pending').first()
    
    if cart_item:
        # If the product is already in the cart, update its quantity
        cart_item.quantity += quantity
        cart_item.save()
        messages.info(request, f"{product.product} quantity updated in your cart.")
        return
    else:
        # Otherwise, add a new CartItem
        CartItem.objects.create(
            cart = cart,
            product = product,
            quantity = quantity,
            total = product.price * quantity,
            status = 'pending',
        )
        messages.success(request, f"{product.product} added to your cart.")
        return

# View: Empty cart
def clear_cart_view(request, name):
    the_shop = get_shop(name)
    cart_items = Cart.objects.filter(is_deleted=False, status='pending', shop=the_shop, customer=request.user)

    if request.method == 'POST':
        cart_items.update(is_deleted=True)
        messages.success(request, 'Cart cleared.')
        return redirect('cart', the_shop)
    return render(request, 'shop/clear_cart.html', {})


# View: Add product to wishlist
def add_to_wishlist(request, name, product_no):
    # Get the shop
    the_shop = get_shop(name)
    
    # Get the product from the shop
    product = get_object_or_404(Inventory, product_id=product_no, shop=the_shop)
    
    # Ensure the user has a wishlist cart
    wishlist, created = Cart.objects.get_or_create(
        shop=the_shop,
        customer=request.user,
    )

    # Check if the product is already in the wishlist
    if CartItem.objects.filter(cart=wishlist, product=product, status='in_wishes').exists():
        messages.info(request, f"{product.name} is already in your wishlist.")
        return

    # Check if the product is already in the user's active cart
    active_cart = Cart.objects.filter(shop=the_shop, customer=request.user).first()
    if active_cart and CartItem.objects.filter(cart=active_cart, product=product, status='pending').exists():
        messages.info(request, f"{product.name} is already in your cart.")
        return

    # Add the product to the wishlist
    CartItem.objects.create(
        cart = wishlist,
        product = product,
        quantity = 1,
        total = product.price,
        status = 'in_wishes',
    )
    messages.success(request, f"{product.name} added to your wishlist.")

# View: Shop homepage
def index(request, name):
    try:
        # Retrieve the shop and user profile
        shop = get_shop(name)
        profile = get_object_or_404(Profile, user=request.user)

        # Fetch categories
        categories = Category.objects.filter(shop=shop)
        top_categories = categories.order_by('total_sales')[:4]
        f_categories = categories.filter(is_featured=True).order_by('timestamp')[:3]

        # Fetch products from top categories(tc) excluding those in the user's pending cart
        my_cart = get_object_or_404(Cart, shop=shop, customer=request.user)
        cart_products = CartItem.objects.filter(cart=my_cart, is_deleted=False, status='pending').values_list('cart_id', flat=True)
        tc_products = []

        for t in top_categories:
            cat = get_object_or_404(Category, category=t.category)
            products = Inventory.objects.filter(shop=shop, category=cat).exclude(product_id__in=cart_products)[:3]
            for p in products:
                tc_products.append(p)

        # Fetch the 2 most recent deals of the day
        deals = TodaysDeal.objects.filter(shop=shop).order_by('time')[:2]
        active_deals = []
        for d in deals:
            logger.debug(f'dl: {d}')
            if d.time > datetime.now(timezone(timedelta(hours=3))):
                active_deals.append(d)

        # Fetch latest arrivals
        products = Inventory.objects.filter(shop=shop)
        arrivals = products.order_by('timestamp')[:4]

        # Fetch 4 featured products
        f_products = products.filter(is_featured=True).order_by('timestamp')[:4]
        
        if request.method == 'POST':
            logger.debug(request.POST)
            prod_id = request.POST.get('id')
            source = request.POST.get('source')
            logger.debug(f'posted')
            logger.debug(f'src: {source}')
            if source == 'add_to_wishlist':
                add_to_wishlist(request, shop.name, prod_id)
                return redirect('shop', shop.name)
        # Prepare context for rendering
        context = {
            'profile': profile,
            'top_categories': top_categories,
            'f_categories': f_categories,
            'f_products': f_products,
            'tc_products': tc_products,
            'deals': active_deals,
            'new_arrivals': arrivals,
            'shop': shop,
        }
        return render(request, 'shop/index.html', context)
    
    except Exception as e:
        # Log the error and show a friendly error page
        logger.error(f"An Error occured while rendering the shop '{name}': {e}")
        messages.error(request, "An error occurred while loading the shop. Please try again later.")
        return redirect('home')  # Adjust this to redirect to an appropriate fallback page


# View: Products list
@login_required
def products_view(request, name):
    sort_by = request.GET.get('sort_by', 'newest')
    show_count = int(request.GET.get('show', 12))
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    the_shop = get_shop(name)

    # Get all product IDs in the current user's cart for this shop
    cart_items = CartItem.objects.filter(
        cart__shop = the_shop,
        cart__customer = request.user,
        status = 'pending'
    ).values_list('product_id', flat=True)

    # Get all products excluding the ones already in the user's cart
    products = Inventory.objects.filter(
        is_deleted = False,
        status = 'available',
        shop = the_shop
    ).exclude(id__in=cart_items)


    categories = Category.objects.filter(is_deleted=False, shop=the_shop).annotate(
        product_count=Count('inventory')
    )
    grouped_products = [
        {
            'category': c,
            'c_products': products.filter(category=c),
            'count': c.product_count,
        }
        for c in categories
    ]
    # for c in categories:
    #     c_products = products.filter(category=c)
    #     grouped_products.append({
    #         'category': c,
    #         'c_products': c_products,
    #     })
    
    if min_price:
        products = products.filter(price__gte=min_price)
    if max_price:
        products = products.filter(price__lte=max_price)

    match sort_by:
        case 'newest':
            products = products.order_by('-timestamp')
        case 'best_sellers':
            products = products.order_by('-total_sales')
        case 'top_rated':
            products = products.order_by('-rating')
        case 'lowest_price':
            products = products.order_by('price')
        case 'highest_price':
            products = products.order_by('-price')
        case _:
            products = products.order_by('-timestamp')

    products = products[:show_count] # Limit no. of products to display

    if request.method == 'POST':
        prod_id = request.POST.get('id')
        source = request.POST.get('source')

        match source:
            case 'add_to_wishlist':
                add_to_wishlist(request, the_shop.name, prod_id)
                return redirect('products', the_shop.name)
            case 'add_to_cart':
                add_to_cart(request, the_shop.name, prod_id, 1)
                return redirect('products', the_shop.name)

    context = {
        'the_shop': the_shop,
        'products': products,
        'group': grouped_products,
        'sort_by': sort_by,
        'show_count': show_count,
    }
    return render(request, 'shop/products.html', context)

# View: Product details
@login_required
def product_details_view(request, name, pk):
    sort_reviews = request.GET.get('sort_reviews', 'best_ratings')
    the_shop = get_shop(name)
    product = get_object_or_404(Inventory, product_id=pk, shop=the_shop)
    rel_products = Inventory.objects.filter(is_deleted=False, shop=the_shop, category=product.category).exclude(product_id=product.product_id)[:4]
    reviews = Review.objects.filter(productID=product)

    match sort_reviews:
        case 'best_ratings':
            reviews = reviews.order_by('-rating')
        case 'worst_ratings':
            reviews = reviews.order_by('rating')
        case _:
            pass
    
    if request.method == 'POST':
        quantity = int(request.POST.get('quantity', 1))
        email = request.POST.get('email')
        comment = request.POST.get('comment')
        body = request.POST.get('body')
        rating = request.POST.get('rating')
        source = request.POST.get('source')
        referer = request.META.get('HTTP_REFERER')
        
        match source:
            case 'new_review':
                review = Review.objects.create(
                    user = request.user,
                    productID = product,
                    email = email or request.user.email,
                    comment = comment,
                    body = body,
                    rating = rating,
                )
                messages.success(request, 'New review added.')
                return redirect('product_details', the_shop.name, product.product_id)
            case 'add_to_cart':
                add_to_cart(request, the_shop.name, product.product_id, quantity)
                return redirect(referer)
            case _:
                pass

    context = {
        'product': product,
        'the_shop': the_shop,
        'rel_products': rel_products,
        'reviews': reviews,
    }
    return render(request, 'shop/product_details.html', context)

# View: Cart
@login_required
def cart_view(request, name):
    referer = request.META.get('HTTP_REFERER')
    the_shop = get_shop(name)
    my_cart = get_object_or_404(Cart, shop=the_shop, customer=request.user)
    cart_items = CartItem.objects.filter(cart=my_cart, status='pending')
    reg_towns = TownsShipped.objects.filter(is_deleted=False, shop=the_shop)

    if request.method == 'POST':
        cart_ids = request.POST.getlist('cart_pid[]')
        quantities = request.POST.getlist('quantity[]')
        note = request.POST.get('note')
        source = request.POST.get('source')
        town_id = request.POST.get('town')

        if source == 'add_town':
            town = get_object_or_404(TownsShipped, pk=town_id)
            my_cart.town=town
            my_cart.save()
            messages.success(request, 'Shipping costs calculated.')
            return redirect('cart', name=the_shop.name)

        elif source == 'add_note':
            my_cart.note=note
            my_cart.save()
            messages.success(request, 'Delivery note updated.')
            return redirect('cart', name=the_shop.name)

        elif source == 'edit_quantity':
            # Bulk update cart items
            for cart, quantity in zip(cart_ids, quantities):
                try:
                    quantity = max(1, min(int(quantity), 100))
                    product = get_object_or_404(Inventory, product_id=cart)
                    cart_item = cart_items.get(product=product)
                    cart_item.quantity = quantity
                    cart_item.save()
                except (Cart.DoesNotExist, ValueError):
                    messages.error(request, "Invalid cart update request.")

            messages.success(request, "Cart updated successfully.")
            return redirect('cart', name=the_shop.name)
       
        elif source == 'checkout_btn':
            if my_cart.town:
                cart_items.update(status='checkout')
                messages.success(request, 'Please fill the details below to complete checkout.')
                return redirect('checkout', name=the_shop.name)
            else:
                messages.error(request, 'Please select nearest town and calculate shipping costs.')
                return redirect('cart', name=the_shop.name)

    context = {
        'referer': referer,
        'reg_towns': reg_towns,
        'my_cart': my_cart,
        'cart_items': [{'objects': cart, 'model_name': cart._meta.model_name} for cart in cart_items],
    }
    return render(request, 'shop/cart.html', context)

# View: Checkout
@login_required
def checkout_view(request, name):
    the_shop = get_shop(name)
    my_cart = get_object_or_404(Cart, shop=the_shop, customer=request.user)
    cart_items = CartItem.objects.filter(cart=my_cart, is_deleted=False, status='checkout')
    addresses = Address.objects.filter(is_deleted=False, shop=the_shop, user=request.user) 
    payment_methods = PaymentMethod.objects.filter(shop=the_shop)

    if not cart_items.exists():
        messages.error(request, "Your cart is empty.")

    if request.method == 'POST':
        phone = request.POST.get('phone')
        email = request.POST.get('email')
        county = request.POST.get('county')
        town = request.POST.get('town')
        address = request.POST.get('address')
        instructions = request.POST.get('instructions')
        payment_method = request.POST.get('payment')
        source = request.POST.get('source')
        addr_id = request.POST.get('addr_id')
        cpn = request.POST.get('coupon')
           
        match source:
            case 'edit_default_addr':
                addresses.update(is_default=False)
                obj = get_object_or_404(Address, pk=addr_id)
                obj.is_default = True
                obj.save()
                messages.success(request, 'Default address updated.')
                return redirect('checkout', the_shop.name)
            case 'coupon_form':
                coupon = get_object_or_404(Coupon, coupon_id=cpn)
                if coupon and coupon.is_active:
                    my_cart.coupon = coupon
                    my_cart.save()
                    messages.success(request, '{coupon.percent_off}% discount applied.')
                    return redirect('checkout', the_shop.name)
                else:
                    messages.error(request, 'Please check coupon number.')
                    return redirect('checkout', the_shop.name)
            case 'checkout':
                delivery, created = Delivery.objects.get_or_create(username=request.user, shop=the_shop)
                delivery.note = my_cart.note
                delivery.town = my_cart.town
                delivery.save()
                for i in cart_items:
                    # product = get_object_or_404(shop=the_shop, product=cart_items.product.product)
                    DeliveryItem.objects.create(
                        delivery = delivery,
                        product = cart_item.product,
                        quantity = cart_item.quantity
                    )
                cart_items.update(status='checked_out', checked_out=datetime.now())
                messages.success(request, f"Check out completed.")
                return redirect('shop', name=the_shop)
    
    try:
        default_addr = addresses.get(is_default=True)
    except Exception:
        default_addr = None

    context = {
        'the_shop': the_shop,
        'addresses': addresses,
        'default_addr': default_addr,
        'payment_methods': payment_methods,
        'my_cart': my_cart,
        'cart_items': [{'objects': cart, 'model_name': cart._meta.model_name} for cart in cart_items],
    }
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
    wishes = Cart.objects.filter(is_deleted=False, shop=the_shop, customer=request.user, status='in_wishes')

    if request.method == 'POST':
        wish_item = request.POST.get('id')
        source = request.POST.get('source')
        quantity = 1

        if source == 'add_to_cart':
            cart_item = get_object_or_404(Cart, product__product_id=wish_item)
            cart_item.status = 'pending'
            cart_item.save()
            messages.success(request, 'Product added to cart.')
            return redirect('wishlist', name=the_shop.name)

    context = {
        'the_shop': the_shop,
        'wishes': wishes,
    }
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


@login_required
# @method_decorator(login_required, name='dispatch')
def delete_view(request, name, model_name, object_id):
    """
    Universal delete view for any model.
    Parameters:
        app_label: The name of the app (e.g., 'shop').
        model_name: The name of the model (e.g., 'Product').
        object_id: The ID of the object to delete.
    """
    referer = request.META.get('HTTP_REFERER')

    try:
        # Get the model class
        content_type = ContentType.objects.get(model=model_name.lower())
        model = content_type.model_class()

        # Get the object instance
        obj = get_object_or_404(model, id=object_id)

        # Check user permissions (Optional: Customize this logic)
        if not request.user.is_superuser and hasattr(obj, 'shop'):
            if obj.shop != request.user.profile.shop:
                return HttpResponseForbidden("You do not have permission to delete this item.")

        if request.method == 'POST':
            # obj.delete()
            obj.is_deleted = True
            obj.save()
            messages.success(request, f"{obj} has been deleted.")
            return redirect(request.POST.get('referer_url'))  # Adjust redirection as needed

        # Render a confirmation page
        context = {
            'object': obj,
            'model_name': model_name,
            'referer': referer,
        }
        return render(request, 'shop/delete.html', context)

    except ContentType.DoesNotExist:
        messages.error(request, "Invalid model type.")
        return redirect(referer) # Adjust redirection as needed


@login_required
def my_addresses_view(request, name):
    the_shop = get_shop(name)
    addresses = Address.objects.filter(is_deleted=False, shop=the_shop, user=request.user)

    if request.method == 'POST':
        county = request.POST.get('county')
        town = request.POST.get('town')
        street = request.POST.get('street')
        house = request.POST.get('house')
        source = request.POST.get('source')
        address = request.POST.get('id')
        set_default = request.POST.get('set_default')

        if source == 'new_address':
            Address.objects.create(
                shop = the_shop,
                user = request.user,
                county = county,
                town = town,
                street = street,
                house = house,
            )
            messages.success(request, 'New address created.')
            return redirect('shop_addresses', the_shop.name)

        elif source == 'edit_address':
            addr = get_object_or_404(Address, pk=address)
            addr.county = county
            addr.town = town
            addr.street = street
            addr.house = house
            if set_default:
                addresses.update(is_default=False)
                addr.is_default = True
            addr.save()
            messages.success(request, 'Address updated.')
            return redirect('shop_addresses', the_shop.name)

    context = {
        'addresses': addresses,
    }
    return render(request, 'shop/my_addresses.html', context)


