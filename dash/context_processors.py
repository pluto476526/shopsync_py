# views/context_processors.py

from django.shortcuts import get_object_or_404
from django.contrib import messages
from django.db.models import Q
from dash.models import Delivery
from shop.models import Shop
import logging

logger = logging.getLogger(__name__)

def get_user_shop(request):
    return get_object_or_404(Shop, owner=request.user)

def get_order(request):
    """
    Context processor to fetch and filter orders based on a query parameter.
    """
    if request.user.is_authenticated:
        query = request.GET.get('q')
        orders = []

        if query:
            orders = Delivery.objects.filter(shop=get_user_shop(request))
            orders = orders.filter(Q(order_number__icontains=query))

            if not orders.exists():
                orders = []
                messages.error(request, f'Order number "{query}" not found.')

        context = {'tracked_order': orders}
        return context

    return {}
