from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.models import User
from django.db import models
from dash.models import Category, Inventory, Supplier, Delivery, ShopStaff
from shop.models import Shop
from datetime import datetime
import logging


# Get logger
logger = logging.getLogger(__name__)

# Get users shop
def my_shop(request):
    shop = get_object_or_404(Shop, owner=request.user)
    return shop

# Create your views here.

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

    products = Inventory.objects.filter(shop=my_shop(request))
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
    context = {'available_products': available_products, 'dash_requests': dash_requests, 'cart_requests': cart_requests}
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

        if source == 'assign_driver':
            order = get_object_or_404(Delivery, id=order_id)

            if address:
                order.address = address

            order.driver = driver
            order.admin = request.user
            order.time_in_transit = datetime.now()
            order.status = 'in_transit'
            order.save()
            messages.success(request, f'Delivery {order.order_number} assigned to {order.driver.name}')
            return redirect('confirmed_deliveries')

        elif source == 'assign_multiple':
            mult_orders = Delivery.objects.filter(order_number=order_no)
            
            for o in mult_orders:
                o.status = 'in_transit'
                o.time_in_transit = datetime.now()
                o.driver = driver
                o.admin = request.user

            Delivery.objects.bulk_update(mult_orders, ['status', 'time_in_transit','driver', 'admin'])
            messages.success(request, f'Delivery #{order_no} assigned to {driver}')
            return redirect('confirmed_deliveries')
 
        elif source == 'complete':
            order = get_object_or_404(Delivery, id=order_id)
            order.status = 'completed'
            order.time_completed = datetime.now()
            order.save()
            messages.success(request, f'Order {order.order_number} completed')
            return redirect('confirmed_deliveries')

    my_drivers = ShopStaff.objects.filter(shop=my_shop(request), job='driver')
    all_deliveries = Delivery.objects.filter(shop=my_shop(request), status='confirmed')
    dash_deliveries = all_deliveries.filter(source='dash')
    cart_deliveries = all_deliveries.filter(source='cart').values('order_number', 'status').annotate(
        total_amount=models.Sum('total'),
        item_count=models.Count('id')
    )
    in_transit = Delivery.objects.filter(shop=my_shop(request), status='in_transit')
    completed = Delivery.objects.filter(shop=my_shop(request), status='completed')
    context = {'dash_deliveries': dash_deliveries, 'cart_deliveries': cart_deliveries, 'my_drivers': my_drivers, 'in_transit': in_transit, 'completed': completed}
    return render(request, 'dash/confirmed_deliveries.html', context)


def track_order_view(request):
    context = {}
    return render(request, 'dash/track_order.html', context)


def order_details_view(request, order_id):
    orders = Delivery.objects.filter(order_number=order_id)
    context = {'orders': orders}
    return render(request, 'dash/order_details.html', context)




