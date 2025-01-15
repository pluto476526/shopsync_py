from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.contenttypes.models import ContentType
from django.http import HttpResponseForbidden
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_http_methods
from django.db import transaction, models
from shop.models import Shop, ShopHelpDesk
from main.models import MainHelpDesk
from datetime import datetime, timedelta, timezone
import logging
from dash.models import (
    Category,
    Inventory,
    Supplier,
    Delivery,
    PaymentMethod,
    Coupon,
    Profile,
    Role,
    Units,
    LowStockThreshold,
    TodaysDeal,
)

# Logger setup
logger = logging.getLogger(__name__)

def get_user_shop(request):
    """Retrieve the shop associated with the current user's profile."""
    try:
        profile = Profile.objects.get(user=request.user)
        shop = Shop.objects.get(name=profile.shop.name)
        return shop
    except (Profile.DoesNotExist, Shop.DoesNotExist) as e:
        logger.error(f"Error retrieving shop: {e}")
        messages.error(request, "Shop not found.")
        return None


def percent_off(price, sale):
    """Calculate percentage off for a price."""
    try:
        return (float(sale) / 100) * float(price)
    except (ValueError, TypeError) as e:
        logger.error(f"Invalid input for percent_off: {e}")
        return 0


def index(request):
    context = {}
    return render(request, 'dash/index.html', context)


@require_http_methods(["GET", "POST"])
def categories(request):
    shop = get_user_shop(request)
    if not shop:
        return redirect('error_page')  # Handle case where shop is not found.

    if request.method == 'POST':
        category_name = request.POST.get('category', '').strip()
        description = request.POST.get('description', '').strip()
        avatar = request.FILES.get('avatar')
        source = request.POST.get('source', '').strip()
        category_id = request.POST.get('category_id')
        is_featured = request.POST.get('is_featured', '').lower() == 'true'

        if not category_name or not source:
            messages.error(request, "Category name and source are required.")
            return redirect('categories')

        try:
            with transaction.atomic():
                if source == 'new_category':
                    Category.objects.create(
                        shop=shop,
                        category=category_name,
                        description=description,
                    )
                    messages.success(request, "Category added successfully.")
                elif source == 'edit_category':
                    category = get_object_or_404(Category, id=category_id)
                    category.category = category_name
                    category.description = description
                    if is_featured:
                        category.is_featured = is_featured
                    if avatar:
                        category.avatar = avatar
                    category.save()
                    messages.success(request, f"{category_name} updated successfully.")
        except Exception as e:
            logger.error(f"Error in category operation: {e}")
            messages.error(request, "Failed to process the category.")
        return redirect('categories')

    my_categories = Category.objects.filter(shop=shop)
    return render(request, 'dash/categories.html', {'categories': my_categories})

@require_http_methods(["GET", "POST"])
def inventory_view(request):
    try:
        shop = get_user_shop(request)
        if not shop:
            return redirect('error_page')

        if request.method == 'POST':
            product_name = request.POST.get('product', '').strip()
            category_name = request.POST.get('category', '').strip()
            description = request.POST.get('description', '').strip()
            quantity = request.POST.get('quantity')
            units = request.POST.get('units', '').strip()
            price = request.POST.get('price')
            is_featured = request.POST.get('is_featured', '').lower() == 'true'
            source = request.POST.get('source', '').strip()
            product_id = request.POST.get('id')
            avatar = request.FILES.get('avatar')

            if not product_name or not source:
                messages.error(request, "Product name and source are required.")
                return redirect('inventory')

            with transaction.atomic():
                category, _ = Category.objects.get_or_create(category=category_name, shop=shop)
                unit = get_object_or_404(Units, units=units)

                if source == 'edit_product':
                    product = get_object_or_404(Inventory, id=product_id)
                    product.product = product_name
                    product.category = category
                    product.description = description
                    product.quantity = quantity
                    product.units = unit
                    product.price = price
                    product.is_featured = is_featured
                    if avatar:
                        product.avatar = avatar
                    product.save()
                    messages.success(request, f"{product_name} updated successfully.")
                elif source == 'new_product':
                    Inventory.objects.create(
                        shop=shop,
                        product=product_name,
                        category=category,
                        description=description,
                        quantity=quantity,
                        units=unit,
                        price=price,
                        is_featured=is_featured,
                        **({"avatar": avatar} if avatar else {}),
                    )
                    messages.success(request, f"{product_name} added successfully.")

            return redirect('inventory')

        products = Inventory.objects.filter(shop=shop, status='available')
        categories = Category.objects.filter(shop=shop)
        units = Units.objects.filter(shop=shop)
        context = {
            'products': products,
            'categories': categories,
            'units': units
        }
        return render(request, 'dash/inventory.html', context)

    except Exception as e:
        logger.error(f"Error in inventory operation: {e}")
        messages.error(request, "Failed to process the inventory.")
        return redirect('inventory')

@transaction.atomic
def orders_view(request):
    shop = get_user_shop(request)
    if not shop:
        return redirect('error_page')  # Handle missing shop case.

    if request.method == 'POST':
        product = request.POST.get('product', '').strip()
        product_id = request.POST.get('product_id')
        category_name = request.POST.get('category', '').strip()
        instr = request.POST.get('instructions', '').strip()
        quantity = request.POST.get('quantity')
        p_units = request.POST.get('units', '').strip()
        source = request.POST.get('source', '').strip()
        supplier_name = request.POST.get('supplier', '').strip()
        order_id = request.POST.get('id')

        try:
            if supplier_name:
                supplier, _ = Supplier.objects.get_or_create(shop=shop, name=supplier_name)

            if category_name:
                category, _ = Category.objects.get_or_create(shop=shop, category=category_name)

            if p_units:
                p_unit, _ = Units.objects.get_or_create(shop=shop, units=p_units)
            
            if source == 'new_order':
                Inventory.objects.create(
                    shop = shop,
                    supplier = supplier,
                    product = product,
                    category = category,
                    order_instructions = instr,
                    order_amount = quantity,
                    units = p_unit,
                    status = 'ordered',
                    available = False,
                    in_orders = True,
                )
                messages.success(request, f"Order for {quantity} {p_units} of {product} prepared.")

            elif source == 'new_order2':
                prod_instance = get_object_or_404(Inventory, product_id=product_id)
                prod_instance.order_amount = quantity
                prod_instance.in_orders = True
                prod_instance.supplier = supplier
                prod_instance.order_instructions = instr
                prod_instance.save()
                messages.success(request, f"Order for {prod_instance.quantity} {prod_instance.product} prepared.")

            elif source == 'edit_order':
                order = get_object_or_404(Inventory, id=order_id)
                order.supplier = supplier or order.supplier
                order.product = product
                order.category = category or order.category
                order.order_instructions = instr
                order.order_amount = quantity
                order.units = p_unit or order.units
                order.save()
                messages.success(request, f"Order for {order.quantity} {order.units.units} of {order.product} edited.")

            elif source == 'receive':
                order = get_object_or_404(Inventory, id=order_id)
                order.status = 'available'
                order.quantity += order.order_amount
                order.order_amount = 0
                order.in_orders = False
                order.save()
                messages.success(request, f"{order.quantity} {order.units.units} of {order.product} added to inventory.")

        except Exception as e:
            logger.error(f"Error processing order: {e}")
            messages.error(request, "Failed to process the order.")

        return redirect('orders')

    try:
        th = LowStockThreshold.objects.get(shop=shop)
        threshold = th.threshold
    except Exception:
        threshold = 0
    low_stocks = Inventory.objects.filter(shop=shop, quantity__lt=threshold)
    categories = Category.objects.filter(shop=shop)
    orders = Inventory.objects.filter(shop=shop, in_orders=True)
    suppliers = Supplier.objects.filter(shop=shop)
    units = Units.objects.filter(shop=shop)
    context = {
        'products': orders,
        'categories': categories,
        'suppliers': suppliers,
        'low_stock_products': low_stocks,
        'units': units,
    }
    return render(request, 'dash/orders.html', context)

@transaction.atomic
def deliveries_view(request):
    shop = get_user_shop(request)
    if not shop:
        return redirect('error_page')

    if request.method == 'POST':
        customer = request.POST.get('username', '').strip()
        quantity = request.POST.get('quantity')
        source = request.POST.get('source', '').strip()
        order_id = request.POST.get('id')
        phone = request.POST.get('phone', '').strip()
        order_no = request.POST.get('order_number', '').strip()
        product_id = request.POST.get('product_id')

        try:
            user = None
            if customer:
                user = User.objects.filter(username=customer).first()

            if source == 'new_delivery':
                selected_product = get_object_or_404(Inventory, product_id=product_id)
                if int(quantity) <= selected_product.quantity:
                    Delivery.objects.create(
                        shop=shop,
                        username=user,
                        unregistered_user=customer,
                        order_number=order_no,
                        prod_id=selected_product.product_id,
                        category=selected_product.category,
                        product=selected_product,
                        quantity=quantity,
                        price=float(selected_product.price) - float(selected_product.discount),
                        units=selected_product.units,
                        total=(float(selected_product.price) - float(selected_product.discount)) * float(quantity),
                        phone=phone,
                    )
                    selected_product.quantity -= int(quantity)
                    selected_product.save()
                    messages.success(request, f"Delivery for {quantity} {selected_product.units} of {selected_product.product} created.")
                else:
                    messages.error(request, f"Only {selected_product.quantity} {selected_product.units} available.")
            elif source == 'confirm_delivery':
                delivery = get_object_or_404(Delivery, id=order_id)
                delivery.status = 'confirmed'
                delivery.time_confirmed = datetime.now()
                delivery.admin = request.user
                delivery.save()
                sale_category = get_object_or_404(Category, category=delivery.category.category)
                sale_category.total_sales += delivery.total
                sale_category.save()
                shop.total_sales += delivery.total
                shop.save()
                messages.success(request, f"Delivery for {delivery.quantity} {delivery.product.product} confirmed.")
            elif source == 'confirm_multiple':
                mult_orders = Delivery.objects.filter(order_number=order_no)
                mult_orders.update(status='confirmed', time_confirmed=datetime.now(), admin=request.user)
                for o in mult_orders:
                    logger.debug(o)
                    category = get_object_or_404(Category, category=o.category.category)
                    category.total_sales += o.total
                    category.save()
                    shop.total_sales += o.total
                    shop.save()
                messages.success(request, f"Order #{order_no} confirmed.")

        except Exception as e:
            logger.error(f"Error processing delivery: {e}")
            messages.error(request, "Failed to process the delivery.")

        return redirect('deliveries')

    requests = Delivery.objects.filter(shop=shop, status='processing')
    dash_requests = requests.filter(source='dash')
    cart_requests = requests.filter(source='cart').values('order_number', 'status').annotate(
        total_quantity=models.Sum('quantity'),
        total_price=models.Sum('price'),
        item_count=models.Count('id')
    )
    available_products = Inventory.objects.filter(shop=shop, status='available')
    context = {
        'available_products': available_products,
        'dash_requests': dash_requests,
        'cart_requests': cart_requests,
    }
    return render(request, 'dash/deliveries.html', context)


@transaction.atomic
def confirmed_deliveries_view(request):
    shop = get_user_shop(request)
    if not shop:
        return redirect('error_page')

    if request.method == 'POST':
        address = request.POST.get('address', '').strip()
        source = request.POST.get('source', '').strip()
        order_id = request.POST.get('id')
        driver_name = request.POST.get('driver', '').strip()
        order_no = request.POST.get('order_number', '').strip()

        try:
            with transaction.atomic():
                driver = None
                if driver_name:
                    driver, created = User.objects.get_or_create(username=driver_name)
                    if created:
                        messages.info(request, f"Driver {driver_name} created.")

                if source == 'assign_multiple':
                    mult_orders = Delivery.objects.filter(order_number=order_no)
                    if address:
                        for order in mult_orders:
                            order.address = address
                    mult_orders.update(
                        status='in_transit',
                        time_in_transit=datetime.now(),
                        driver=driver,
                        admin=request.user
                    )
                    messages.success(request, f"Delivery #{order_no} assigned to {driver}.")
                elif source == 'complete_multiple':
                    Delivery.objects.filter(order_number=order_no).update(
                        status='completed',
                        time_completed=datetime.now(),
                        admin=request.user
                    )
                    messages.success(request, f"Order #{order_no} marked as completed.")
        except Exception as e:
            messages.error(request, f"Error processing delivery: {e}")
        return redirect('confirmed_deliveries')

    all_deliveries = Delivery.objects.filter(shop=shop)
    confirmed_deliveries = all_deliveries.filter(status='confirmed').values('order_number').annotate(
        total_amount=models.Sum('total'),
        item_count=models.Count('id')
    )
    in_transit = all_deliveries.filter(status='in_transit').values('order_number').annotate(
        total_amount=models.Sum('total'),
        item_count=models.Count('id')
    )
    completed_deliveries = all_deliveries.filter(status='completed').values('order_number').annotate(
        total_amount=models.Sum('total'),
        item_count=models.Count('id')
    )
    my_drivers = User.objects.filter(groups__name='Drivers'),  # Assuming a Driver group exists.
    context = {
        'confirmed_deliveries': confirmed_deliveries,
        'deliveries_in_transit': in_transit,
        'completed_deliveries': completed_deliveries,
        'my_drivers': my_drivers,
    }
    return render(request, 'dash/confirmed_deliveries.html', context)


def track_order_view(request):
    return render(request, 'dash/track_order.html', {})


def order_details_view(request, order_id):
    orders = Delivery.objects.filter(order_number=order_id)
    if not orders.exists():
        messages.error(request, f"No orders found for Order ID {order_id}.")
        return redirect('orders')
    return render(request, 'dash/order_details.html', {'orders': orders})


def online_sales_view(request):
    shop = get_user_shop(request)
    if not shop:
        return redirect('error_page')

    sales = Delivery.objects.filter(shop=shop, source='cart', status='completed')
    online_sales = sales.values('order_number').annotate(
        total_amount=models.Sum('total'),
        item_count=models.Count('id')
    )
    return render(request, 'dash/online_sales.html', {'sales': online_sales})


@transaction.atomic
def physical_sales_view(request):
    try:
        shop = get_user_shop(request)
        if not shop:
            return redirect('error_page')

        if request.method == 'POST':
            customer = request.POST.get('username', '').strip()
            phone = request.POST.get('phone', '').strip()
            product_no = request.POST.get('product_id')
            quantity = request.POST.get('quantity', 0)
            order_no = request.POST.get('order_number', '').strip()
            payment_method = request.POST.get('payment_method', '').strip()
            source = request.POST.get('source', '').strip()

            with transaction.atomic():
                if source == 'new_sale':
                    sel_product = get_object_or_404(Inventory, product_id=product_no)
                    if int(quantity) > sel_product.quantity:
                        messages.error(request, f"Insufficient stock for {sel_product.product}.")
                        return redirect('physical_sales')

                    payments = get_object_or_404(PaymentMethod, shop=shop, method=payment_method)
                    totals = float(quantity) * float(sel_product.price)
                    Delivery.objects.create(
                        shop=shop,
                        unregistered_user=customer,
                        order_number=order_no,
                        product=sel_product,
                        prod_id=sel_product.id,
                        category=sel_product.category,
                        quantity=quantity,
                        price=sel_product.price,
                        units=sel_product.units,
                        total=totals,
                        phone=phone,
                        payment_method=payments,
                        source='in_shop',
                    )
                    sel_product.quantity -= int(quantity)
                    sel_product.save()
                    sale_category = get_object_or_404(Category, category=sel_product.category.category)
                    sale_category.total_sales += totals
                    sale_category.save()
                    shop.total_sales += totals
                    shop.save()
                    messages.success(request, f"Order {order_no} created. Please confirm payment.")
                    return redirect('physical_sales')
                elif source == 'confirm_payment':
                    Delivery.objects.filter(shop=shop, order_number=order_no).update(
                        status='completed',
                        time_completed=datetime.now(),
                        admin=request.user
                    )
                    messages.success(request, f"Order {order_no} payment confirmed.")
                    return redirect('physical_sales')

        context = {
            'available_products': Inventory.objects.filter(shop=shop, status='available'),
            'p_method': PaymentMethod.objects.filter(shop=shop),
            'pending_sales': Delivery.objects.filter(shop=shop, source='in_shop', status='processing').values(
                'order_number').annotate(
                total_amount=models.Sum('total'),
                item_count=models.Count('id'),
            ),
            'completed_sales': Delivery.objects.filter(shop=shop, source='in_shop', status='completed').values(
                'order_number').annotate(
                total_amount=models.Sum('total'),
                item_count=models.Count('id'),
            ),
        }
        return render(request, 'dash/physical_sales.html', context)
    except Exception as e:
        messages.error(request, 'Error processing sale.')
        logger.error(f"Error processing sale: {e}")
        return redirect('physical_sales')

def main_helpdesk_view(request):
    shop = get_user_shop(request)
    if not shop:
        return redirect('error_page')

    tickets = MainHelpDesk.objects.filter(username=request.user)

    if request.method == 'POST':
        issue = request.POST.get('issue', '').strip()
        description = request.POST.get('description', '').strip()
        phone = request.POST.get('phone', '').strip()
        email = request.POST.get('email', '').strip()
        source = request.POST.get('source', '').strip()

        if source == 'new_ticket':
            MainHelpDesk.objects.create(
                shop=shop,
                username=request.user,
                issue=issue,
                description=description,
                phone=phone,
                email=email,
            )
            messages.success(request, "Ticket generated.")
            return redirect('main_helpdesk_user')

    return render(request, 'dash/main_helpdesk.html', {'tickets': tickets})


def shop_helpdesk_view(request):
    shop = get_user_shop(request)
    if not shop:
        return redirect('error_page')

    issues = ShopHelpDesk.objects.filter(shop=shop)
    pending_issues = issues.filter(is_sorted=False)
    sorted_issues = issues.filter(is_sorted=True)

    if request.method == 'POST':
        status = request.POST.get('status', '').strip()
        is_sorted = request.POST.get('is_sorted', '').lower() == 'true'
        source = request.POST.get('source', '').strip()
        tkt_id = request.POST.get('id')

        if source == 'change_status':
            ticket = get_object_or_404(ShopHelpDesk, id=tkt_id)
            ticket.status = status
            ticket.is_sorted = is_sorted
            ticket.admin = request.user
            ticket.save()
            messages.success(request, f"Ticket {ticket.help_id}: {status}")
            return redirect('shop_helpdesk')

    context = {'issues': pending_issues, 'sorted_issues': sorted_issues}
    return render(request, 'dash/shop_helpdesk.html', context)

@transaction.atomic
def shop_profile_view(request):
    shop = get_user_shop(request)
    if not shop:
        return redirect('error_page')

    staff_roles = Role.objects.filter(shop=shop)
    units = Units.objects.filter(shop=shop)
    pm_methods = PaymentMethod.objects.filter(shop=shop)
    try:
        threshold = get_object_or_404(LowStockThreshold, shop=shop)
    except Exception:
        threshold = None

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        bio = request.POST.get('bio', '').strip()
        location = request.POST.get('location', '').strip()
        address = request.POST.get('address', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()
        insta = request.POST.get('instagram', '').strip()
        twitter = request.POST.get('twitter', '').strip()
        avatar = request.FILES.get('avatar')
        image1 = request.FILES.get('image1')
        image2 = request.FILES.get('image2')
        title1 = request.POST.get('title1', '').strip()
        title2 = request.POST.get('title2', '').strip()
        title3 = request.POST.get('title3', '').strip()
        role = request.POST.get('role_name', '').strip()
        new_units = request.POST.get('units', '').strip()
        ls_threshold = request.POST.get('ls_threshold', '').strip()
        new_pm_method = request.POST.get('p_mthd')
        source = request.POST.get('source', '').strip()

        with transaction.atomic():
            if source == 'update_profile':
                shop.name = name
                shop.bio = bio
                shop.location = location
                shop.address = address
                shop.email = email
                shop.phone = phone
                shop.instagram = insta
                shop.twitter = twitter

                if avatar:
                    shop.avatar = avatar
                if image1:
                    shop.image1 = image1
                if image2:
                    shop.image2 = image2

                shop.save()
                messages.success(request, 'Shop profile updated.')

            elif source == 'settings_form':
                shop.title1 = title1
                shop.title2 = title2
                shop.title3 = title3
                shop.save()

                if role:
                    Role.objects.create(shop=shop, role_name=role)
                    messages.success(request, f'Staff role "{role}" added.')

                if new_units:
                    Units.objects.create(shop=shop, units=new_units)
                    messages.success(request, f'Product units "{new_units}" added.')

                if new_pm_method:
                    PaymentMethod.objects.create(shop=shop, method=new_pm_method)
                    messages.success(request, f'Payment method "{new_pm_method}" added.')

                if ls_threshold:
                    if threshold:
                        threshold.threshold = ls_threshold
                        threshold.save()
                    else:
                        LowStockThreshold.objects.create(shop=shop, threshold=ls_threshold)
                        messages.success(request, f'Low stock threshold set at "{ls_threshold}".')

                messages.success(request, "Settings updated.")

        return redirect('shop_profile')

    context = {
        'my_shop': shop,
        'staff_roles': staff_roles,
        'units': units,
        'threshold': threshold,
        'p_methods': pm_methods or []
    }
    return render(request, 'dash/shop_profile.html', context)


def deals_and_promos_view(request):
    shop = get_user_shop(request)
    all_products = Inventory.objects.filter(shop=shop)
    coupons = Coupon.objects.filter(shop=shop)
    all_categories = Category.objects.filter(shop=shop)

    if request.method == 'POST':
        product = request.POST.get('product')
        amount = request.POST.get('amount')
        source = request.POST.get('source')
        category_name = request.POST.get('category')
        coupon_id = request.POST.get('coupon_id')
        duration = request.POST.get('duration')
        deal_no = request.POST.get('deal_id')

        if product:
            product_instance = get_object_or_404(Inventory, product_id=product)

        if category_name:
            category_instance = get_object_or_404(Category, shop=shop, category=category_name)

        if source == 'new_discount':
            product_instance.discount = amount
            product_instance.in_deals = True
            product_instance.in_discount = True
            product_instance.price = float(product_instance.price) - float(amount)
            product_instance.save()
            messages.success(request, f'KSH. {amount} discount set for {product_instance.product}. Please confirm price.')
            return redirect('deals_and_promos')

        elif source == 'new_percent_off':
            product_instance.discount = percent_off(product_instance.price, amount)
            product_instance.in_deals = True
            product_instance.in_sale = True
            product_instance.percent_off = amount
            product_instance.price = float(product_instance.price) - float(product_instance.discount)
            product_instance.save()
            messages.success(request, f'{amount}% discount set for {product_instance.product}. Please confirm current price.')
            return redirect('deals_and_promos')

        elif source == 'new_category_sale':
            category_products = all_products.filter(category=category_instance)

            for product in category_products:
                product.discount = percent_off(product.price, int(amount))
                product.in_deals = True
                product.percent_off = amount
                product.price = float(product.price) - float(product.discount)

            Inventory.objects.bulk_update(category_products, ['discount', 'in_deals', 'percent_off', 'price'])
            category_instance.in_sale = True
            category_instance.percent_off = amount
            category_instance.save()
            messages.success(request, f'{amount}% discount set for all products in {category_name}. Please confirm current prices.')
            return redirect('deals_and_promos')

        elif source == 'new_coupon':
            Coupon.objects.create(
                shop = shop,
                percent_off = amount,
            )
            messages.success(request, f'Coupon for {amount}% off on all shopping generated.')
            return redirect('deals_and_promos')

        elif source == 'new_todays_deal':
            product_instance.price = float(product_instance.price) - float(amount)
            product_instance.in_deals = True
            product_instance.discount = amount
            product_instance.save()

            new = TodaysDeal.objects.create(
                shop = shop,
                product_id = product_instance.product_id,
                product = product_instance.product,
                price = product_instance.price - float(amount),
                category = product_instance.category.category,
                avatar = product_instance.avatar,
                discount = amount,
                time = datetime.now(timezone(timedelta(hours=3))) + timedelta(hours=int(duration)+3)
            )
            logger.debug(f'time: {new.time}')
            logger.debug(f'delta: {timedelta(hours=int(duration))}')
            logger.debug(f'now: {datetime.now(timezone(timedelta(hours=3)))}')
            messages.success(request, f'{product_instance.product} saved as deal of the day')
            return redirect('deals_and_promos')

        elif source == 'cancel_discount':
            product_instance.in_deals = False
            product_instance.in_sale = False
            product_instance.in_discount = False
            product_instance.price += product_instance.discount
            product_instance.percent_off = 0
            product_instance.discount = 0
            product_instance.save()
            messages.success(request, f'Discount for {product_instance.product} cancelled. Please confirm current prices.')
            return redirect('deals_and_promos')

        elif source == 'cancel_all_discounts':
            products = all_products.filter(in_discount=True)

            for p in products:
                p.in_deals = False
                p.in_discount = False
                p.price += p.discount
                p.discount = 0

            Inventory.objects.bulk_update(products, ['in_deals', 'in_discount', 'discount', 'price'])
            messages.success(request, 'All discounts cancelled. Please confirm current prices.')
            return redirect('deals_and_promos')

        elif source == 'cancel_all_sales':
            products = all_products.filter(in_sale=True)

            for p in products:
                p.in_deals = False
                p.in_sale = False
                p.price += p.discount
                p.discount = 0
                p.percent_off = 0

            Inventory.objects.bulk_update(products, ['in_deals', 'in_sale', 'discount', 'percent_off', 'price'])
            messages.success(request, 'All discounts cancelled. Please confirm current prices.')
            return redirect('deals_and_promos')

        elif source == 'cancel_category_sale':
            products = all_products.filter(category=category_instance)

            for p in products:
                p.in_deals = False
                p.in_sale = False
                p.price += p.discount
                p.discount = 0
                p.percent_off = 0

            Inventory.objects.bulk_update(products, ['in_deals', 'in_sale', 'discount', 'percent_off', 'price'])
            category_instance.in_sale = False
            category_instance.percent_off = 0
            category_instance.save()
            messages.success(request, f'Sale for {category_instance.category} cancelled. Please confirm current prices.')
            return redirect('deals_and_promos')

        elif source == 'cancel_all_category_sales':
            categories = all_categories.filter(in_sale=True)

            for c in categories:
                products = all_products.filter(category=c)

                for p in products:
                    p.in_deals = False
                    p.in_sale = False
                    p.price += p.discount
                    p.discount = 0
                    p.percent_off = 0

                Inventory.objects.bulk_update(products, ['in_deals', 'in_sale', 'discount', 'percent_off', 'price'])
                c.in_sale = False
                c.percent_off = 0
                c.save()

            messages.success(request, 'All category sales cancelled. Please confirm prices.')
            return redirect('deals_and_promos')


        elif source == 'cancel_coupon':
            coupon = get_object_or_404(Coupon, coupon_id=coupon_id)
            coupon.status = 'inactive'
            coupon.save()
            messages.success(request, f'Coupon #{coupon_id} deactivated.')
            return redirect('deals_and_promos')

        elif source == 'cancel_all_coupons':
            for coupon in coupons:
                coupon.status = 'inactive'

            Coupon.objects.bulk_update(coupons, ['status'])
            messages.success(request, 'All coupons deactivated.')
            return redirect('deals_and_promos')

        elif source == 'deactivate_todays_deal':
            deal = get_object_or_404(TodaysDeal, id=deal_no)
            deal.status = 'inactive'
            deal.save()

            product = get_object_or_404(Inventory, product_id=deal.product_id)
            product.price += deal.discount
            product.discount = 0
            product.in_deals = False
            product.save()

            messages.success(request, f'Deal for {product.product} deactivated. Please confirm current price.')
            return redirect('deals_and_promos')

    todays_deals = TodaysDeal.objects.filter(shop=shop, is_deleted=False)
    categories_no_sale = all_categories.filter(in_sale=False)
    available_products = all_products.filter(in_deals=False)
    in_discounts = all_products.filter(in_discount=True)
    in_sales = all_products.filter(in_sale=True)
    category_sales = all_categories.filter(in_sale=True)
    context = {
        'all_products': all_products,
        'products': available_products,
        'categories': categories_no_sale,
        'in_discounts': in_discounts,
        'in_sales': in_sales,
        'category_sales': category_sales,
        'coupons': coupons,
        'todays_deals': [{'object': d,'app_label': d._meta.app_label, 'model_name': d._meta.model_name} for d in todays_deals],
    }
    return render(request, 'dash/deals_and_promos.html', context)


@transaction.atomic
def staff_view(request):
    shop = get_user_shop(request)
    if not shop:
        return redirect('error_page')

    staff = Profile.objects.filter(shop=shop, in_staff=True, is_deleted=False)
    roles = Role.objects.filter(shop=shop, is_deleted=False)

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        role_name = request.POST.get('role', '').strip()
        source = request.POST.get('source', '').strip()

        if source == 'new_staff' and password1 == password2:
            with transaction.atomic():
                user = User.objects.create_user(username=username, email=email, password=password1)
                role = get_object_or_404(Role, shop=shop, role_name=role_name)
                Profile.objects.create(shop=shop, user=user, in_staff=True, role=role)
                messages.success(request, "New staff member created.")
                return redirect('dash_staff')
        else:
            messages.error(request, "Password mismatch or invalid input.")
    
    context = {'staff': staff, 'roles': roles}
    return render(request, 'dash/staff.html', context)



# @method_decorator(login_required, name='dispatch')
def delete_view(request, app_label, model_name, object_id):
    """
    Universal delete view for any model.
    Parameters:
        app_label: The name of the app (e.g., 'shop').
        model_name: The name of the model (e.g., 'Product').
        object_id: The ID of the object to delete.
    """
    referer = request.META.get('HTTP_REFERER')
    logger.debug(referer)

    try:
        # Get the model class
        content_type = ContentType.objects.get(app_label=app_label, model=model_name.lower())
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
            messages.success(request, f"{model_name} with ID {object_id} has been deleted.")
            return redirect(request.POST.get('referer'))  # Adjust redirection as needed

        # Render a confirmation page
        context = {'object': obj, 'model_name': model_name, 'referer': referer}
        return render(request, 'dash/dash_delete.html', context)

    except ContentType.DoesNotExist:
        messages.error(request, "Invalid model type.")
        return redirect(referer) # Adjust redirection as needed


