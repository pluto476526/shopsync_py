from django.db.models import Q
from django.shortcuts import get_object_or_404
from shop.models import Shop
import logging


# Get logger
logger = logging.getLogger(__name__)


def get_company(request):
    if request.user.is_authenticated:
        try:
            shop = get_object_or_404(Shop, owner=request.user)

        except:
            shop = []

    else:
        shop = []

    context = {'shop': shop}
    return context




