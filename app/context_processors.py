# context_processors.py
# Create this file in your app directory (e.g., myapp/context_processors.py)
from django_user_agents.utils import get_user_agent
from .models import Category, Pitch

def categories_context(request):
    """
    Context processor to make categories available in all templates
    """
    categories = (Category.objects
                 .filter(pitches__isnull=False)
                 .distinct()
                 .order_by('name'))  # Optional: order categories alphabetically
    
    return {
        'categories': categories
    }
    
def device_context(request):
    """
    Context processor to make device information available in all templates
    """
    user_agent = get_user_agent(request)
    return {
        'is_mobile': user_agent.is_mobile,
        'is_tablet': user_agent.is_tablet,
        'is_pc': user_agent.is_pc,
        'is_touch_capable': user_agent.is_touch_capable,
        'browser': user_agent.browser.family,
        'os': user_agent.os.family,
        'device': user_agent.device.family,
    }

# FEATURED PITCHES
def featured_pitches_context(request):
    featured_pitches = (Pitch.objects
                       .filter(is_featured=True)
                       .select_related('category')
                       .order_by('-rank')[:2])
    return {
        'featured_pitches': featured_pitches
    }
