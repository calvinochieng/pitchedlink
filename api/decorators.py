# decorators.py
from functools import wraps
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import APIKey

def api_key_required(view_func):
    """Decorator to require API key authentication"""
    @csrf_exempt
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        # Check for API key in header
        api_key = request.META.get('HTTP_X_API_KEY') or request.META.get('HTTP_AUTHORIZATION')
        
        # Handle Bearer token format
        if api_key and api_key.startswith('Bearer '):
            api_key = api_key[7:]
        
        # Authenticate
        auth_result = APIKey.authenticate(api_key)
        if not auth_result:
            return JsonResponse({'error': 'Invalid or missing API key'}, status=401)
        
        # Add API key info to request
        request.api_key = auth_result
        request.user = auth_result.user
        
        return view_func(request, *args, **kwargs)
    return wrapper
