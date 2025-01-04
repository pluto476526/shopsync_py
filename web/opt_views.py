from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.db.models import Q
from shop.models import Shop, ShopCategory
from dash.models import Profile, Category
from web.forms import UserRegistrationForm
import logging

logger = logging.getLogger(__name__)

def home(request):
    try:
        profile = get_object_or_404(Profile, user=request.user)
    except TypeError:
        profile = None

    if request.method == 'POST':
        if request.user.is_authenticated:
            name = request.POST.get('name', '').strip()
            bio = request.POST.get('bio', '').strip()
            category = request.POST.get('category')
            source = request.POST.get('source')

            if source == 'new_shop':
                try:
                    category_instance = ShopCategory.objects.get(category=category)
                    shop = Shop.objects.create(
                        owner=request.user,
                        name=name,
                        bio=bio,
                        shop_category=category_instance,
                    )
                    profile.shop = shop
                    profile.save()
                    messages.success(request, f'{name} successfully registered.')
                except ShopCategory.DoesNotExist:
                    messages.error(request, 'Selected category does not exist.')
                except Exception as e:
                    logger.error(f"Error creating shop: {e}")
                    messages.error(request, 'An error occurred while creating the shop.')
                return redirect('home')
        else:
            messages.warning(request, "You must be logged in to create a shop.")
    
    shops = Shop.objects.all()
    shop_categories = ShopCategory.objects.all()
    context = {
        'available_shops': shops,
        'shop_categories': shop_categories,
        'profile': profile,
    }
    return render(request, 'web/index.html', context)


def register(request):
    if request.user.is_authenticated:
        return redirect('home')

    register_form = UserRegistrationForm(request.POST or None)
    if request.method == 'POST' and register_form.is_valid():
        register_form.save()
        messages.success(request, 'Registration successful. Please sign in.')
        return redirect('sign_in')

    context = {'register_form': register_form}
    return render(request, 'web/register.html', context)


def sign_in(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()

        user = authenticate(request, username=username, password=password)
        if user:
            logger.info(f"Authenticated user: {user}")
            Profile.objects.get_or_create(user=user)
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, 'Invalid username or password.')

    context = {'login_form': AuthenticationForm()}
    return render(request, 'web/sign_in.html', context)


def sign_out(request):
    logger.info(f"Logged out user: {request.user}")
    logout(request)
    return redirect('home')


def all_shops_view(request):
    q = request.GET.get('q', '').strip()
    all_shops = Shop.objects.exclude(owner=request.user) if request.user.is_authenticated else Shop.objects.all()

    if q:
        all_shops = all_shops.filter(
            Q(name__icontains=q) |
            Q(shop_category__category__icontains=q) |
            Q(owner__username__icontains=q)
        )

    context = {'all_shops': all_shops}
    return render(request, 'web/all_shops.html', context)


def shop_details_view(request, name):
    selected_shop = get_object_or_404(Shop, name=name)
    categories = Category.objects.filter(shop=selected_shop)
    context = {'selected_shop': selected_shop, 'categories': categories}
    return render(request, 'web/shop_details.html', context)

