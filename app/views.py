from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

import json
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.contrib import messages


from django.core.mail import send_mail
from urllib.parse import urlparse
from django.db.models import F
from django.views.decorators.csrf import csrf_exempt

from .models import *
from django.core.paginator import Paginator
from django_user_agents.utils import get_user_agent


from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.utils.html import escape

# Main Page Views



def index(request):
    # Get user agent information
    current_page = 'index'

    # Complete fields list matching template usage
    # Use 'category_id' instead of 'category' when using only() with select_related()
    common_fields = [
        'id', 'name', 'title', 'description', 'slug', 
        'icon_url', 'banner_url', 'url', 'source',
        'category_id',  # Changed from 'category' to 'category_id'
        'rank', 'clap', 'created_at',
        'is_featured', 'is_launched'
    ]
    
    # If you need category fields in your template, include them explicitly
    category_fields = ['category__name', 'category__slug']
    
    # Get featured pitches (high rank)
    featured_pitches = (Pitch.objects
                       .filter(is_featured=True)
                       .select_related('category')
                       .only(*(common_fields + category_fields))
                       .order_by('-rank')[:2])

    
    # Get top ranked pitches for leaderboard
    top_pitches = (Pitch.objects
                  .select_related('category')
                  .only(*(common_fields + category_fields))
                  .order_by('-rank')[:10])
    
    # Get new pitches (recently added)
    new_pitches = (Pitch.objects
                  .select_related('category')
                  .only(*(common_fields + category_fields))
                  .order_by('-created_at')[:16])
    
    paginator = Paginator(new_pitches, 16)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get distinct categories with at least one pitch
    categories = (Category.objects
                 .filter(pitches__isnull=False)
                 .distinct()
                 .order_by('name'))
                 
    # categories = (Category.objects
    #              .filter(pitches__isnull=False)
    #              .distinct())           
    
    # Add device information to context
    context = {
        'featured_pitches': featured_pitches,
        'top_pitches': top_pitches,
        'new_pitches': page_obj,
        'pitches': page_obj,
        'categories': categories,
        'current_page': current_page,
            }
    
    return render(request, 'pitches/list.html', context)

# One funtion that returns new and pitches based on filters with pagination 



@require_http_methods(["GET"])
def pitches(request):
    current_page = 'pitches'
    # Get query parameters
    action = request.GET.get('action', '')
    
    # Fix: Convert page to integer with proper error handling
    try:
        page = int(request.GET.get('page', 1))
    except (ValueError, TypeError):
        page = 1
    
    # Base queryset
    pitches_qs = Pitch.objects.all().order_by('-created_at')
    
    # Pagination
    paginator = Paginator(pitches_qs, 20)
    try:
        page_obj = paginator.page(page)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)
    
    # Check if it's an AJAX request or explicitly requesting JSON
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.GET.get('format') == 'json':
        # Serialize the pitches
        pitches_list = []
        for pitch in page_obj:
            pitch_data = {
                'id': pitch.id,
                'slug': pitch.slug,
                'name': escape(pitch.name),  # Fix: Escape HTML
                'title': escape(pitch.title),  # Fix: Escape HTML
                'handle': pitch.pitch_data[0]['user']['handle'],
                'description': escape(pitch.description) if pitch.description else None,  # Fix: Escape HTML
                'banner_url': pitch.banner_url if pitch.banner_url else None,
                'url': pitch.url,
                'icon_url': pitch.icon_url if pitch.icon_url else None,
                'category': pitch.category.name if pitch.category else None,
                'mention_count': pitch.mention_count,
                'rank': pitch.rank,
                'clap': pitch.clap,
                'created_at': pitch.created_at.isoformat(),
                'updated_at': pitch.updated_at.isoformat(),
                'claimed': pitch.claimed,
            }
            
            # Fix: Better handling of pitch_data
            if hasattr(pitch, 'pitch_data') and pitch.pitch_data:
                try:
                    pitch_data['pitch_data'] = pitch.pitch_data[0] if len(pitch.pitch_data) > 0 else None
                except (IndexError, TypeError):
                    pitch_data['pitch_data'] = None
            
            pitches_list.append(pitch_data)
        
        return JsonResponse({
            'success': True,
            'pitches': pitches_list,
            'pagination': {
                'has_next': page_obj.has_next(),
                'has_previous': page_obj.has_previous(),
                'page_number': page_obj.number,
                'num_pages': paginator.num_pages,
                'count': paginator.count,
            }
        })
    
    # Regular HTML response
    return render(request, 'pitches/pitches.html', {
        'current_page': current_page,
        'pitches': page_obj,
        'action': action
    })


#Site SEO optimized home page
def home(request):
    current_page = 'home'
    top_pitches = Pitch.objects.all().order_by('-rank')[:9]
    context = {
        'top_pitches': top_pitches,
        'current_page': current_page,
    }
    return render(request, 'index.html', context)

#Categories View
def categories(request):
    """
    Display all categories with their respective pitches.
    """
    current_page = 'categories'
    # Get all distinct categories
    categories = Pitch.objects.values_list('category', flat=True).distinct()
    
    # Get pitches for each category
    category_pitches = {}
    for category in categories:
        pitches = Pitch.objects.filter(category=category).order_by('-rank')[:5]
        category_pitches[category] = pitches
    
    return render(request, 'pitches/categories/categories.html', {
        'categories': categories,
        'category_pitches': category_pitches,
        'current_page': current_page,
    })

# Category Detail View
def category_detail(request, slug):
    """
    Display pitches filtered by category.
    """
    current_page = 'category detail'
    category = get_object_or_404(Category, slug=slug)
    # Get pitches in the specified category
    pitches = Pitch.objects.filter(category=category).order_by('-rank')
    
    # Pagination for category pitches
    paginator = Paginator(pitches, 20)  # Show 20 pitches per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'pitches/categories/category_detail.html', {
        'current_page': current_page,
        'pitches': page_obj,
        'category_name': category.name,
    })


def leaderboard(request):
    """
    Display a leaderboard of top pitches based on their rank with infinite scroll support.
    """
    current_page = 'leaderboard'
    # Get page number from request, default to 1
    page = request.GET.get('page', 1)
    
    # Get all pitches ordered by rank
    pitches = Pitch.objects.all().order_by('-rank')
    
    # Pagination - 10 items per page
    paginator = Paginator(pitches, 20)
    
    try:
        page_obj = paginator.page(page)
    except:
        page_obj = paginator.page(1)
    
    # Calculate the starting rank for this page
    start_rank = (page_obj.number - 1) * paginator.per_page + 1
    
    # If it's an AJAX request, return JSON
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        from django.template.loader import render_to_string
        
        html = render_to_string('pitches/partials/leaderboard_items.html', {
            'top_pitches': page_obj,
            'start_rank': start_rank,
        })
        
        return JsonResponse({
            'html': html,
            'has_next': page_obj.has_next(),
            'next_page_number': page_obj.next_page_number() if page_obj.has_next() else None
        })
    
    # Get all categories
    categories = Category.objects.all().order_by('name')
    
    # For initial page load
    return render(request, 'pitches/leaderboard.html', {
        'current_page': current_page,
        'top_pitches': page_obj,
        'categories': categories,
        'start_rank': start_rank,
            })


def detail(request, slug):
    """
    Display detailed information about a specific pitch.
    Optimized for SEO with rich metadata and structured data.
    """
    # Get the pitch by slug or return a 404 if not found
    pitch = get_object_or_404(Pitch, slug=slug)
    
    # Extract engagement data from pitch_data JSON field
    engagement_data = {}
    source_data = {}
    
    if pitch.pitch_data and isinstance(pitch.pitch_data, list) and len(pitch.pitch_data) > 0:
        first_entry = pitch.pitch_data[0]
        engagement_data = first_entry.get("engagement", {})
        source_data = {
            'user': first_entry.get("user", {}),
            'timestamp': first_entry.get("timestamp", {}),
            'tweet_text': first_entry.get("tweetText", ""),
            'reply_link': first_entry.get("replyLink", ""),
            'links': first_entry.get("links", [])
        }
    
    # Get related pitches (same category or similar ranking)
    related_pitches = Pitch.objects.filter(
        category=pitch.category
    ).exclude(
        id=pitch.id
    ).order_by('rank')[:10]
    
    # If not enough related pitches, get some by ranking
    if related_pitches.count() < 10:
        additional_pitches = Pitch.objects.exclude(
            id=pitch.id
        ).exclude(
            id__in=[p.id for p in related_pitches]
        ).order_by('rank')[:10-related_pitches.count()]
        related_pitches = list(related_pitches) + list(additional_pitches)
    
    # Calculate pitch metrics for display
    total_engagement = sum([
        engagement_data.get('replies', 0),
        engagement_data.get('retweets', 0),
        engagement_data.get('likes', 0)
    ])
    
    # SEO metadata
    meta_data = {
        'title': f"{pitch.name} | PitchedLink",
        'description': pitch.description[:160] if pitch.description else f"Discover {pitch.name}, a trending startup pitch on PitchedLink. View details, rankings, and engagement metrics.",
        'keywords': f"{pitch.name}, startup pitch, {pitch.category or 'software'}, trending startups, pitch deck",
        'canonical_url': request.build_absolute_uri(),
        'og_image': pitch.banner_url or pitch.icon_url,
        'og_type': 'article',
        'twitter_card': 'summary_large_image',
    }
    
    # Structured data for rich snippets
    structured_data = {
        "@context": "https://schema.org",
        "@type": "SoftwareApplication",
        "name": pitch.name,
        "operatingSystem": "All",
        "applicationCategory": pitch.category.name or "WebApplication",
        "description": pitch.description or f"Discover {pitch.name}, a trending SaaS tool.",
        "url": pitch.url,
        "image": pitch.banner_url or pitch.icon_url,
        "aggregateRating": {
            "@type": "AggregateRating",
            "ratingValue": min(5, max(1, 5 - (pitch.rank / 20))),
            "reviewCount": max(1, pitch.clap),
            "bestRating": 5,
            "worstRating": 1
        },
        "offers": {
            "@type": "Offer",
            "price": "0",  # If free trial or unknown, keep 0
            "priceCurrency": "USD",
            "availability": "https://schema.org/InStock" if pitch.is_launched else "https://schema.org/PreOrder"
        },
        "author": {
            "@type": "Person",
            "name": pitch.pitch_data[0]['user'].get('name'),
            "url": f"https://x.com/{pitch.pitch_data[0]['user'].get('handle')}"
        },
        "datePublished": pitch.updated_at.strftime("%Y-%m-%dT%H:%M:%SZ") 
        

    }
    
    context = {
        'pitch': pitch,
        'engagement_data': engagement_data,
        'source_data': source_data,
        'related_pitches': related_pitches,
        'total_engagement': total_engagement,
        'meta_data': meta_data,
        'structured_data': json.dumps(structured_data),
        # Extras
        
        'latest_mention': pitch.get_latest_mention(),
        'total_engagement': pitch.get_engagement_data(),
    }
    
    return render(request, 'pitches/detail.html', context)


@require_http_methods(["POST"])
@login_required
def clap_pitch(request, slug):
    try:
        data = json.loads(request.body)
        clap_count = max(1, int(data.get('clap_count', 1)))

        pitch = get_object_or_404(Pitch, slug=slug)
        pitch.add_clap(user=request.user, clap_count=clap_count)

        # 👉 Show raw claps in UI — feels better
        display_claps = pitch.get_clap_count()

        return JsonResponse({
            'success': True,
            'display_claps': display_claps,  # 👈 Big number for UI
            'rank': pitch.rank               # 👈 Real rank (based on effective claps)
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

def pricing(request):
    return render(request, 'pricing.html')


def about(request):
    return render(request, 'about.html')

def blog(request):
    # If you have a Blog model:
    # posts = BlogPost.objects.filter(published=True).order_by('-created_at')
    return render(request, 'blog.html', {
        # 'posts': posts
    })

# Legal Pages
def terms_of_service(request):
    return render(request, 'legal/terms.html')

def privacy_policy(request):
    return render(request, 'legal/privacy.html')

def refund_policy(request):
    return render(request, 'legal/refund.html')

# Support Views
def contact(request):
    if request.method == 'POST':
        # Process contact form
        name = request.POST.get('name')
        email = request.POST.get('email')
        message = request.POST.get('message')
        
        send_mail(
            f"Contact Form Submission from {name}",
            message,
            email,
            [settings.DEFAULT_FROM_EMAIL],
            fail_silently=False,
        )
        messages.success(request, "Your message has been sent!")
        return redirect('contact')
    
    return render(request, 'support/contact.html')


