# shop/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.contenttypes.models import ContentType
from django.contrib import messages
from django.db.models import Sum, Count, F
from django.db import transaction
from django.contrib.auth.decorators import login_required
from shop.models import Shop, Cart, CartItem, ShopHelpDesk, CountyShipped, Address
from dash.models import Inventory, Category, PaymentMethod, Delivery, DeliveryItem, TodaysDeal, Profile, Review, Coupon
from datetime import datetime, timedelta, timezone
import logging
import secrets
import string


# Logger setup
logger = logging.getLogger(__name__)

# Helper function: Retrieve a shop by name
def get_shop(name):
    return get_object_or_404(Shop, name=name)


# Helper: Add product to cart
def add_to_cart(request, name, product_no, quantity=1):
    # Get the shop
    the_shop = get_shop(name)
    
    # Get the product
    product = get_object_or_404(Inventory, product_id=product_no)
    
    # Ensure the user has an active cart
    cart, created = Cart.objects.get_or_create(
        shop = the_shop,
        customer = request.user,
        status = 'processing',
    )

    # Check if the product is already in the cart
    cart_item = CartItem.objects.filter(cart=cart, product=product).first()
    
    if cart_item:
        messages.info(request, f'{product.product} is already in your cart.')
        return
    else:
        # Otherwise, add a new CartItem
        CartItem.objects.create(
            cart = cart,
            product = product,
            quantity = quantity,
        )
        messages.success(request, f"{product.product} added to your cart.")
        return

# View: Empty cart
def clear_cart_view(request, name):
    the_shop = get_shop(name)
    my_cart = Cart.objects.filter(shop=the_shop, customer=request.user, status='processing', is_deleted=False).first()
    cart_items = CartItem.objects.filter(cart=my_cart)

    if request.method == 'POST':
        cart_items.update(is_deleted=True)
        messages.success(request, 'Cart cleared.')
        return redirect('cart', the_shop)
    return render(request, 'shop/clear_cart.html', {})


# HELPER: Add product to wishlist
def add_to_wishlist(request, name, product_no):
    # Get the shop
    the_shop = get_shop(name)
    
    # Get the product
    product = get_object_or_404(Inventory, product_id=product_no)
    
    # Ensure the user has an active cart
    cart, created = Cart.objects.get_or_create(
        shop = the_shop,
        customer = request.user,
        status = 'in_wishes',
    )

    # Check if the product is already in the wish list
    wish_item = CartItem.objects.filter(cart=cart, product=product).first()
    
    if wish_item:
        messages.info(request, f'{product.product} is already in your wish list.')
        return
    else:
        # Otherwise, add a new CartItem
        CartItem.objects.create(
            cart = cart,
            product = product,
            quantity = 1,
        )
        messages.success(request, f"{product.product} added to your wish list.")
        return


# View: Add to cart from the index page
def add_to_cart_view(request, name, product_id):
    shop = get_shop(name)
    add_to_cart(request, shop.name, product_id)
    return redirect(request.META.get('HTTP_REFERER'))
    context = {}
    return render(request, 'empty.html', context)


# View: Add to wishlist from the index page
def add_to_wishlist_view(request, name, product_id):
    shop = get_shop(name)
    add_to_wishlist(request, shop.name, product_id)
    return redirect(request.META.get('HTTP_REFERER'))
    context = {}
    return render(request, 'empty.html', context)


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
        my_cart = Cart.objects.filter(shop=shop, customer=request.user, status='processing').first()
        cart_products = CartItem.objects.filter(cart=my_cart, is_deleted=False).values_list('product_id', flat=True)
        
        tc_products = []
        for t in top_categories:
            cat = get_object_or_404(Category, category=t.category)
            products = Inventory.objects.filter(shop=shop, category=cat, is_deleted=False).exclude(id__in=cart_products)[:3]
            for p in products:
                tc_products.append(p)

        # Fetch the 2 most recent deals of the day
        deals = TodaysDeal.objects.filter(shop=shop).order_by('time')[:2]
        active_deals = []
        for d in deals:
            if d.time > datetime.now(timezone(timedelta(hours=3))):
                active_deals.append(d)

        # Fetch latest arrivals
        products = Inventory.objects.filter(shop=shop).exclude(id__in=cart_products)
        arrivals = products.order_by('timestamp')[:4]

        # Fetch 4 featured products
        f_products = products.filter(is_featured=True).order_by('timestamp')[:4]
        
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
            # 'referer': request.META.get('HTTP_REFERER')
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
    
    # Get shop object
    the_shop = get_shop(name)

    # Current users cart for this shop
    my_cart = Cart.objects.filter(shop=the_shop, customer=request.user, status='processing').first()

    # Get all product IDs in the current user's cart for this shop
    cart_items = CartItem.objects.filter(cart=my_cart).values_list('product_id', flat=True)

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
    my_cart = Cart.objects.filter(shop=the_shop, customer=request.user, status='processing').first()
    cart_items = CartItem.objects.filter(cart=my_cart)
    counties = CountyShipped.objects.filter(is_deleted=False, shop=the_shop)

    if request.method == 'POST':
        cart_ids = request.POST.getlist('cart_pid[]')
        quantities = request.POST.getlist('quantity[]')
        note = request.POST.get('note')
        source = request.POST.get('source')
        cnty_id = request.POST.get('county')

        if source == 'add_county':
            county = get_object_or_404(CountyShipped, pk=cnty_id)
            my_cart.county = county
            my_cart.save()
            messages.success(request, 'Shipping costs calculated.')
            return redirect('cart', name=the_shop.name)

        elif source == 'add_note':
            my_cart.note = note
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
            if my_cart.county:
                my_cart.status = 'checkout'
                my_cart.save()
                messages.success(request, 'Please fill the details below to complete checkout.')
                return redirect('checkout', name=the_shop.name)
            else:
                messages.error(request, 'Please select your county and calculate shipping costs.')
                return redirect('cart', name=the_shop.name)

    context = {
        'referer': referer,
        'counties': counties,
        'my_cart': my_cart,
        'cart_items': [{'objects': cart, 'model_name': cart._meta.model_name} for cart in cart_items],
    }
    return render(request, 'shop/cart.html', context)

# View: Checkout
@login_required
def checkout_view(request, name):
    the_shop = get_shop(name)
    addresses = Address.objects.filter(is_deleted=False, shop=the_shop, user=request.user)
    default_addr = addresses.filter(is_default=True).first()
    payment_methods = PaymentMethod.objects.filter(shop=the_shop)
    my_cart = Cart.objects.filter(is_deleted=False, shop=the_shop, customer=request.user, status='checkout').first()
    cart_items = CartItem.objects.filter(cart=my_cart, is_deleted=False)
    
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
                if cpn:
                    coupon = get_object_or_404(Coupon, coupon_id=cpn)
                    if coupon and coupon.is_active:
                        my_cart.coupon = coupon
                        my_cart.save()
                        messages.success(request, f'{coupon.percent_off}% discount applied.')
                        return redirect('checkout', the_shop.name)
                    elif coupon.is_active == False:
                        messages.error(request, 'Coupon is not active.')
                        return redirect('checkout', the_shop.name)
                    else:
                        messages.error(request, 'Please check coupon number.')
                        return redirect('checkout', the_shop.name)
                else:
                    return redirect('checkout', the_shop.name)
            case 'place_order':
                with transaction.atomic():
                    p_method = get_object_or_404(PaymentMethod, id=payment_method)
                    county = get_object_or_404(CountyShipped, id=my_cart.county.id)
                    # Create or get the delivery
                    delivery = Delivery.objects.create(username=request.user, shop=the_shop)
                    delivery.note = my_cart.note
                    delivery.county = county
                    delivery.address = default_addr
                    delivery.payment_method = p_method
                    delivery.total = my_cart.total_price
                    delivery.source = 'cart'
                    delivery.save()

                    # Add items to the delivery
                    for i in cart_items:
                        product = get_object_or_404(Inventory, shop=the_shop, id=i.product.id)
                        DeliveryItem.objects.create(
                            delivery = delivery,
                            product = product,
                            quantity = i.quantity
                        )

                    # Update cart status
                    my_cart.status = 'checked_out'
                    my_cart.checked_out = datetime.now()
                    my_cart.save()

                messages.success(request, 'Check out completed.')
                return redirect('shop', name=the_shop)
            case 'cancel_order':
                my_cart.is_deleted = True
                my_cart.save()
                messages.success(request, 'Order cancelld.')
                return redirect('shop', name=the_shop)

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
    orders = Delivery.objects.filter(shop=the_shop, username=request.user, is_deleted=False)
    context = {'the_shop': the_shop, 'orders': orders}
    return render(request, 'shop/history.html', context)


# View: Order details
@login_required
def order_details_view(request, name, order_id):
    the_shop = get_shop(name)
    order = get_object_or_404(Delivery, order_number=order_id)
    orders = DeliveryItem.objects.filter(delivery=order, is_deleted=False)
    address = Address.objects.filter(shop=the_shop, user=request.user, is_default=True).first()
    shipping = get_object_or_404(CountyShipped, id=order.county.id)
    total_amnt = float(shipping.price) + float(order.total)
    context = {
        'the_shop': the_shop, 
        'order': order,
        'orders': orders,
        'address': address,
        'shipping': shipping,
        'total_amnt': total_amnt,
    }
    return render(request, 'shop/order_details.html', context)


# View: Wishlist
@login_required
def wishlist_view(request, name):
    the_shop = get_shop(name)
    my_carts = Cart.objects.filter(customer=request.user, shop=the_shop, is_deleted=False)
    active_cart = my_carts.filter(status='processing').first()
    cart_items = CartItem.objects.filter(cart=active_cart).values_list('id', flat=True)
    logger.debug(f'cart items: {cart_items}')
    wish_cart = my_carts.filter(status='in_wishes').first()
    wishes = CartItem.objects.filter(cart=wish_cart).exclude(id__in=cart_items)
    if request.method == 'POST':
        wish_item = request.POST.get('id')
        source = request.POST.get('source')

        if source == 'add_to_cart':
            add_to_cart(request, the_shop, wish_item)
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
    return render(request, 'shop/contact_us.html', context)


@login_required
def about_view(request, name):
    the_shop = get_shop(name)
    staff = Profile.objects.filter(shop=the_shop, in_staff=True, is_featured=True)
    context = {
        'the_shop': the_shop,
        'staff': staff,
    }
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

        # Check user permissions
        if not request.user.is_superuser and hasattr(obj, 'shop'):
            if obj.shop != request.user.profile.shop:
                return HttpResponseForbidden("You do not have permission to delete this item.")

        if request.method == 'POST':
            # obj.delete()
            obj.is_deleted = True
            obj.save()
            messages.success(request, f"{obj} has been deleted.")
            return redirect(request.POST.get('referer_url'))

        # Render a confirmation page
        context = {
            'object': obj,
            'model_name': model_name,
            'referer': referer,
        }
        return render(request, 'shop/delete.html', context)

    except ContentType.DoesNotExist:
        messages.error(request, "Invalid model type.")
        return redirect(referer)


@login_required
def my_addresses_view(request, name):
    the_shop = get_shop(name)
    addresses = Address.objects.filter(is_deleted=False, shop=the_shop, user=request.user)
    counties = CountyShipped.objects.filter(is_deleted=False, shop=the_shop)

    if request.method == 'POST':
        county = request.POST.get('county')
        town = request.POST.get('town')
        street = request.POST.get('street')
        house = request.POST.get('house')
        source = request.POST.get('source')
        address = request.POST.get('id')
        set_default = request.POST.get('set_default')

        if source == 'new_address':
            cnty = get_object_or_404(CountyShipped, id=county)
            Address.objects.create(
                shop = the_shop,
                user = request.user,
                county = cnty,
                town = town,
                street = street,
                house = house,
            )
            messages.success(request, f'New address in {cnty.county}, {town} created.')
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
        'counties': counties,
    }
    return render(request, 'shop/my_addresses.html', context)


# View: return single items page
def returns_view(request, name, order_id):
    shop = get_shop(name)
    delivery = get_object_or_404(Delivery, order_number=order_id)
    delivery_items = DeliveryItem.objects.filter(delivery=delivery, status='none', is_deleted=False)

    if request.method == 'POST':
        item_ids = request.POST.getlist('item_id[]')
        return_note = request.POST.get('return_note')
        source = request.POST.get('source')
        
        match source:
            case 'return_items':
                with transaction.atomic():
                    if return_note:
                        delivery.return_note = return_note
                        delivery.save()

                    for i in item_ids:
                        item = delivery_items.filter(id=i).first()
                        item.status = 'returned'
                        item.save()
                        messages.success(request, f'{item.product.product} set for return.')
                    return redirect('returns_page', shop.name, order_id)
    context = {
        'delivery_items': delivery_items,
    }
    return render(request, 'shop/returns_page.html', context)


# View: Returns and cancellations
def returns_and_cancellations_view(request, name):
    shop = get_shop(name)
    my_deliveries = Delivery.objects.filter(shop=shop, username=request.user)
    returns = my_deliveries.filter(status='cancelled')
    returned_items = DeliveryItem.objects.filter(delivery__in=my_deliveries, status='returned')
    context = {
        'returns': returns,
        'returned_items': returned_items,
    }
    return render(request, 'shop/returns_and_cancellations.html', context)


# View: Shop mini dashboard -> userstats
def shop_dash_view(request, name):
    shop = get_shop(name)
    default_addr = Address.objects.filter(shop=shop, user=request.user, is_default=True).first()
    recent_orders = Delivery.objects.filter(shop=shop, username=request.user, is_deleted=False)
    context = {
        'address': default_addr,
        'recent_orders': recent_orders,
    }
    return render(request, 'shop/shop_dash.html', context)



