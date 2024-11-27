# views/context_processors.py

from django.shortcuts import get_object_or_404
from django.contrib import messages
from django.db.models import Q
from dash.models import Delivery
from shop.models import Shop
import logging

logger = logging.getLogger(__name__)

def get_user_shop(user):
    return get_object_or_404(Shop, owner=user)

def get_order(request):
    """
    Context processor to fetch and filter orders based on a query parameter.
    """
    try:
        shop = get_user_shop(request.user)
        orders = Delivery.objects.filter(shop=shop)
        query = request.GET.get('q', '')

        if query:
            orders = orders.filter(Q(order_number__icontains=query))

            if not orders.exists():
                messages.error(request, f'Order number "{query}" not found.')

        else:
            orders = []

        return {'tracked_order': orders}
    
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
        messages.error(request, 'An error occurred while retrieving orders.')
        return {}
