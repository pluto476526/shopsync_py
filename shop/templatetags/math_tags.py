from django import template
from decimal import Decimal

register = template.Library()

@register.simple_tag
def add(*args):
    """
    Custom template tag to add multiple numeric values.
    Ensures all inputs are converted to decimals before addition.
    """
    try:
        # Convert all arguments to Decimal and sum them
        return sum(Decimal(arg) for arg in args)
    except Exception as e:
        # Handle cases where conversion fails (e.g., invalid input)
        return f"Error: {e}"

