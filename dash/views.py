from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.models import User
from django.db import models
from dash.models import Category, Inventory, Supplier, Delivery, ShopStaff, PaymentMethod, HelpDesk
from shop.models import Shop
from datetime import datetime
import logging


# Get logger
logger = logging.getLogger(__name__)

# Get users shop
def my_shop(request):
    return get_object_or_404(Shop, owner=request.user)


# Get % off
def percent_off(price, sale):
    return (float(sale) / 100) * float(price)


def index(request):
    context = {}
    return render(request, 'dash/index.html', context)


def categories(request):
    if request.method == 'POST':
        category_name = request.POST.get('category')
        description = request.POST.get('description')
        avatar = request.FILES.get('avatar')
        source = request.POST.get('source')
        category_id = request.POST.get('category_id')
        is_featured = request.POST.get('is_featured')

        if source == 'new_category':
            Category.objects.create(shop=my_shop(request), category=category_name, description=description)
            messages.success(request, 'Category added')
            return redirect('categories')

        elif source == 'edit_category':
            category = get_object_or_404(Category, id=category_id)
            category.category = category_name
            category.description = description

            if is_featured:
                category.is_featured = is_featured

            if avatar:
                category.avatar = avatar

            category.save()
            messages.success(request, f'{category.category} Category edited')
            return redirect('categories')

    my_categories = Category.objects.filter(shop=my_shop(request))
    context = {'categories': my_categories}
    return render(request, 'dash/categories.html', context)


def inventory_view(request):
    if request.method == 'POST':
        product_name = request.POST.get('product')
        category_name = request.POST.get('category')
        description = request.POST.get('description')
        quantity = request.POST.get('quantity')
        units = request.POST.get('units')
        price = request.POST.get('price')
        is_featured = request.POST.get('is_featured')
        source = request.POST.get('source')
        product_id = request.POST.get('id')
        avatar = request.FILES.get('avatar')
        category, created = Category.objects.get_or_create(category=category_name, shop=my_shop(request))

        if source == 'edit_product':
            product_obj = get_object_or_404(Inventory, id=product_id)
            product_obj.product = product_name
            product_obj.description = description
            product_obj.quantity = quantity
            product_obj.price = price
            product_obj.category = category
            
            if is_featured:
                product_obj.is_featured = is_featured

            if avatar:
                product_obj.avatar = avatar

            if units:
                product_obj.units = units

            product_obj.save()
            messages.success(request, f'{product_obj} edited')
            return redirect('inventory')

        elif source == 'new_product':
            Inventory.objects.create(
                shop = my_shop(request),
                product = product_name,
                category = category,
                description = description,
                quantity = quantity,
                units = units,
                price = price,
                is_featured = is_featured if is_featured else False,
                **({"avatar": avatar} if avatar else {}),
            )
            messages.success(request, f'{product_name} added to inventory')
            return redirect('inventory')

    products = Inventory.objects.filter(shop=my_shop(request), status='available')
    categories = Category.objects.filter(shop=my_shop(request))
    context = {'products': products, 'categories': categories}
    return render(request, 'dash/inventory.html', context)


def orders_view(request):
    if request.method == 'POST':
        product = request.POST.get('product')
        category_name = request.POST.get('category')
        description = request.POST.get('description')
        quantity = request.POST.get('quantity')
        units = request.POST.get('units')
        source = request.POST.get('source')
        supplier_name = request.POST.get('supplier')
        order_id = request.POST.get('id')

        if supplier_name:
            supplier, sup_created = Supplier.objects.get_or_create(name=supplier_name, shop=my_shop(request))

        if category_name:
            category, created = Category.objects.get_or_create(category=category_name, shop=my_shop(request))

        if source == 'new_order':
            Inventory.objects.create(
                shop = my_shop(request),
                supplier = supplier,
                product = product,
                category = category,
                description = description,
                quantity = quantity,
                units = units,
                status = 'ordered',
            )
            messages.success(request, f'Order for {quantity} {units} of {product} prepared')
            return redirect('orders')

        elif source == 'edit_order':
            order = get_object_or_404(Inventory, id=order_id)
            order.supplier = supplier
            order.product = product
            order.category = category
            order.description = description
            order.quantity = quantity

            if units:
                order.units = units

            order.save()
            messages.success(request, f'Order for {quantity} {units} of {product} edited')
            return redirect('orders')

        elif source == 'receive':
            order = get_object_or_404(Inventory, id=order_id)
            order.description = 'None'
            order.status = 'available'
            order.save()
            messages.success(request, f'{order.quantity} {order.units} of {order.product} added to inventory')
            return redirect('orders')

    categories = Category.objects.filter(shop=my_shop(request))
    orders = Inventory.objects.filter(shop=my_shop(request), status='ordered')
    suppliers = Supplier.objects.filter(shop=my_shop(request))
    context = {'products': orders, 'categories': categories, 'suppliers': suppliers}
    return render(request, 'dash/orders.html', context)


def deliveries_view(request):
    if request.method == 'POST':
        customer = request.POST.get('username')
        product = request.POST.get('product')
        quantity = request.POST.get('quantity')
        source = request.POST.get('source')
        order_id = request.POST.get('id')
        phone = request.POST.get('phone')
        order_no = request.POST.get('order_number')

        try:
            username = User.objects.get(username=customer)

        except User.DoesNotExist:
            username = None

        if source == 'new_delivery':
            selected_product = get_object_or_404(Inventory, product=product)
            category_instance = get_object_or_404(Category, category=selected_product.category.category)
            Delivery.objects.create(
                shop = my_shop(request),
                username = username,
                unregistered_user = customer,
                order_number = order_no,
		        prod_id = selected_product.product_id,
                category = category_instance,
                product = selected_product,
                quantity = quantity,
                price = selected_product.price,
                units = selected_product.units,
                total = int(selected_product.price) * int(quantity),
                phone = phone,
            )
            messages.success(request, f'Delivery request for {quantity} {selected_product.units} of {selected_product.product} created')
            return redirect('deliveries')

        elif source == 'confirm_delivery':
            delivery = get_object_or_404(Delivery, id=order_id)
            delivery.status = 'confirmed'
            delivery.time_confirmed = datetime.now()
            delivery.admin = request.user
            delivery.save()
            messages.success(request, f'Delivery request for {delivery.quantity} {delivery.units} of {delivery.product.product} confirmed')
            return redirect('deliveries')

        elif source == 'confirm_multiple':
            mult_orders = Delivery.objects.filter(order_number=order_no)
            
            for o in mult_orders:
                o.status = 'confirmed'
                o.time_confirmed = datetime.now()
                o.admin = request.user

            Delivery.objects.bulk_update(mult_orders, ['status', 'time_confirmed', 'admin'])
            messages.success(request, f'Order /#{order_no} confirmed')
            return redirect('deliveries')
    
    requests = Delivery.objects.filter(shop=my_shop(request), status='processing') 
    dash_requests = requests.filter(source='dash')
    cart_requests = requests.filter(source='cart')
    cart_requests = cart_requests.values('order_number', 'status').annotate(
        total_quantity=models.Sum('quantity'),
        total_price=models.Sum('price'),
        item_count=models.Count('id')
    )
    available_products = Inventory.objects.filter(shop=my_shop(request), status='available')
    context = {
        'available_products': available_products,
        'dash_requests': dash_requests,
        'cart_requests': cart_requests,
    }
    return render(request, 'dash/deliveries.html', context)


def confirmed_deliveries_view(request):
    if request.method == 'POST':
        address = request.POST.get('address')
        source = request.POST.get('source')
        order_id = request.POST.get('id')
        driver_name = request.POST.get('driver')
        order_no = request.POST.get('order_number')

        if driver_name:
            driver, created = ShopStaff.objects.get_or_create(shop=my_shop(request), name=driver_name, job='driver')

        if source == 'assign_multiple':
            mult_orders = Delivery.objects.filter(order_number=order_no)

            if address:
                order.address = address
            
            for order in mult_orders:
                order.status = 'in_transit'
                order.time_in_transit = datetime.now()
                order.driver = driver
                order.admin = request.user

            Delivery.objects.bulk_update(mult_orders, ['status', 'time_in_transit','driver', 'admin'])
            messages.success(request, f'Delivery #{order_no} assigned to {driver}')
            return redirect('confirmed_deliveries')
 
        elif source == 'complete_multiple':
            mult_orders = Delivery.objects.filter(order_number=order_no)

            for order in mult_orders:
                order.status = 'completed'
                order.time_completed = datetime.now()
                order.admin = request.user

            Delivery.objects.bulk_update(mult_orders, ['status', 'time_completed', 'admin'])
            messages.success(request, f'Order #{order.order_number} completed')
            return redirect('confirmed_deliveries')

    my_drivers = ShopStaff.objects.filter(shop=my_shop(request), job='driver')
    all_deliveries = Delivery.objects.filter(shop=my_shop(request))
    confirmed_deliveries = all_deliveries.filter(status='confirmed').values('order_number').annotate(
        total_amount = models.Sum('total'),
        item_count = models.Count('id')
    )
    deliveries_in_transit = all_deliveries.filter(status='in_transit').values('order_number').annotate(
        total_amount = models.Sum('total'),
        item_count = models.Count('id')
    )
    completed_deliveries = all_deliveries.filter(status='completed').values('order_number').annotate(
        total_amount = models.Sum('total'),
        item_count = models.Count('id')
    )
    context = {
        'confirmed_deliveries': confirmed_deliveries,
        'deliveries_in_transit': deliveries_in_transit,
        'completed_deliveries': completed_deliveries,
        'my_drivers': my_drivers,
    }
    return render(request, 'dash/confirmed_deliveries.html', context)


def track_order_view(request):
    context = {}
    return render(request, 'dash/track_order.html', context)


def order_details_view(request, order_id):
    orders = Delivery.objects.filter(order_number=order_id)
    context = {'orders': orders}
    return render(request, 'dash/order_details.html', context)


def online_sales_view(request):
    sales = Delivery.objects.filter(shop=my_shop(request), source='cart', status='completed')  
    online_sales = sales.values('order_number').annotate(
        total_amount = models.Sum('total'),
        item_count = models.Count('id')
    )
    context = {'sales': online_sales}
    return render(request, 'dash/online_sales.html', context)


def physical_sales_view(request):
    if request.method == 'POST':
        customer = request.POST.get('customer')
        phone = request.POST.get('phone')
        product_no = request.POST.get('product_id')
        quantity = request.POST.get('quantity')
        order_no = request.POST.get('order_number')
        payment_method = request.POST.get('payment_method')
        source = request.POST.get('source')

        if source == 'new_sale':
            sel_product = get_object_or_404(Inventory, product_id=product_no)
            payments = get_object_or_404(PaymentMethod, shop=my_shop(request), payment_method=payment_method)
            category = get_object_or_404(Category, shop=my_shop(request), category=sel_product.category.category)
            Delivery.objects.create(
                shop = my_shop(request),
                unregistered_user = customer,
                order_number = order_no,
                product = sel_product,
                prod_id = sel_product.product_id,
                category = category,
                quantity = quantity,
                price = sel_product.price,
                units = sel_product.units,
                total = float(quantity) * float(sel_product.price),
                phone = phone,
                payment_method = payments,
                source = 'in_shop',
            )
            messages.success(request, f'Order {order_no} processing. Please confirm payment')
            return redirect('physical_sales')

        elif source == 'confirm_payment':
            mult_orders = Delivery.objects.filter(shop=my_shop(request), order_number=order_no)
            for order in mult_orders:
                order.status = 'completed'
                order.admin = request.user
                order.time_completed = datetime.now()

            Delivery.objects.bulk_update(mult_orders, ['status', 'time_completed', 'admin',])
            messages.success(request, f'Order #{order_no} completed')
            return redirect('physical_sales')

    available_products = Inventory.objects.filter(shop=my_shop(request), status='available')
    pay_method = PaymentMethod.objects.filter(shop=my_shop(request))
    pending_sales = Delivery.objects.filter(
        shop = my_shop(request),
        source = 'in_shop',
        status = 'processing',
    ).values('order_number').annotate(
        total_amount = models.Sum('total'),
        item_count = models.Count('id'),
    )
    completed_sales = Delivery.objects.filter(
        shop = my_shop(request),
        source = 'in_shop',
        status = 'completed',
    ).values('order_number').annotate(
        total_amount = models.Sum('total'),
        item_count = models.Count('id'),
    )
    context = {
        'available_products': available_products,
        'pay_method': pay_method,
        'pending_sales': pending_sales,
        'completed_sales': completed_sales,
    }
    return render(request, 'dash/physical_sales.html', context)


def delete_view(request, pk):
    obj = get_object_or_404(Inventory, shop=my_shop(request), id=pk)

    if request.method == 'POST':
        # Delete product
        obj.delete()
        messages.success(request, f'{obj} deleted')
        return redirect('inventory')

    context = {'obj': obj}
    return render(request, 'dash/delete.html', context)


def user_helpdesk_view(request):
    issues = HelpDesk.objects.filter(username=request.user)
    context = {'issues': issues}
    return render(request, 'dash/helpdesk.html', context)


def shop_profile_view(request):
    shop = my_shop(request)

    if request.method == 'POST':
        name = request.POST.get('name')
        bio = request.POST.get('bio')
        avatar = request.FILES.get('avatar')
        image1 = request.FILES.get('image1')
        image2 = request.FILES.get('image2')
        location = request.POST.get('location')
        address = request.POST.get('address')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        insta = request.POST.get('instagram')
        twitter = request.POST.get('twitter')
        title1 = request.POST.get('title1')
        title2 = request.POST.get('title2')
        source = request.POST.get('source')

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
            return redirect('shop_profile')

        elif source == 'settings_form':
            shop.title1 = title1
            shop.title2 = title2
            shop.save()
            messages.success(request, 'Landing page titles updated.')
            return redirect('shop_profile')

    context = {'my_shop': shop}
    return render(request, 'dash/shop_profile.html', context)


def deals_and_promos_view(request):
    shop = my_shop(request)

    if request.method == 'POST':
        product = request.POST.get('product')
        amount = request.POST.get('amount')
        source = request.POST.get('source')
        product_instance = get_object_or_404(Inventory, product_id=product)

        if source == 'new_discount':
            product_instance.discount = amount
            product_instance.save()
            messages.success(request, f'KSH. {amount} discount set for {product_instance.product}')
            return redirect('deals_and_promos')

        elif source == 'new_percent_off':
            product_instance.discount = percent_off(product_instance.price, amount)
            product_instance.save()
            messages.success(request, f'{amount}% discount set for {product_instance.product}')
            return redirect('deals_and_promos')


    all_products = Inventory.objects.filter(shop=shop, in_deals=False)
    context = {'products': all_products}
    return render(request, 'dash/deals_and_promos.html', context)


















