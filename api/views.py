# views.py
from datetime import timezone
import json
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from .models import APIKey
from .decorators import api_key_required

# Web interface for managing API keys
@login_required
def api_keys_list(request):
    """List user's API keys"""
    api_keys = APIKey.objects.filter(user=request.user)
    return render(request, 'api/api_keys.html', {'api_keys': api_keys})

@require_http_methods(["POST"])
@login_required
def create_api_key(request):
    """Create a new API key"""
    name = request.POST.get('name', '').strip()
    
    if not name:
        return JsonResponse({'error': 'Name is required'}, status=400)
    
    api_key, raw_key = APIKey.generate_key(user=request.user, name=name)
    
    return JsonResponse({
        'success': True,
        'api_key': raw_key,
        'name': api_key.name,
        'prefix': api_key.prefix,
        'message': 'API key created! Save it now - you won\'t see it again.'
    })

@require_http_methods(["POST"])
@login_required
def delete_api_key(request, key_id):
    """Delete/deactivate an API key"""
    api_key = get_object_or_404(APIKey, id=key_id, user=request.user)
    api_key.is_active = False
    api_key.save()
    
    return JsonResponse({'success': True, 'message': 'API key deactivated'})

# API endpoints (examples)
@api_key_required
def api_hello(request):
    """Simple API endpoint"""
    return JsonResponse({
        'message': f'Hello, {request.user.username}!',
        'api_key_name': request.api_key.name,
        'timestamp': timezone.now().isoformat()
    })

@api_key_required
def api_user_info(request):
    """Get user information"""
    return JsonResponse({
        'user': {
            'id': request.user.id,
            'username': request.user.username,
            'email': request.user.email,
            'first_name': request.user.first_name,
            'last_name': request.user.last_name,
        },
        'api_key_info': {
            'name': request.api_key.name,
            'created_at': request.api_key.created_at.isoformat(),
            'last_used': request.api_key.last_used.isoformat() if request.api_key.last_used else None,
        }
    })

@api_key_required
@require_http_methods(["POST"])
def api_create_data(request):
    """Example POST endpoint"""
    try:
        data = json.loads(request.body)
        # Process your data here
        return JsonResponse({
            'success': True,
            'message': 'Data processed successfully',
            'received_data': data,
            'processed_by': request.user.username
        })
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
