# views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count, Sum, Avg
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from django.utils import timezone
from datetime import datetime, timedelta
import json
from .models import Pitch, Category, PitchAnalytics, UserProfile, Claim

@login_required
def dashboard(request):
    user = request.user
    """
    Personalized dashboard view
    """
    current_page = 'dashboard'
    # Get or create user profile
    profile, created = UserProfile.objects.get_or_create(user=user)
    
    # Get user-specific statistics
    user_stats = get_user_stats(request.user)
    # new_pitches = Pitch.objects.filter().order_by('-created_at')[:4]
    
    # Get suggested pitches (based on X handle mentions)
    if profile.x_handle:
        # print(profile.x_handle)
        # Get all pitches that might contain the user's handle (case-insensitive)
        potential_pitches = Pitch.objects.filter(
            pitch_data__icontains=profile.x_handle
        ).exclude(
            claims__user=user
        ).order_by('-rank')[:10]  # Get a few more in case some don't match exactly
        # print(potential_pitches)

        # Filter pitches where the handle is in the user.handle field of pitch_data
        suggested_pitches = [
            pitch for pitch in potential_pitches
            if pitch.pitch_data and 
            any(
                isinstance(item, dict) and 
                item.get('user', {}).get('handle', '').lower() == profile.x_handle.lower()
                for item in (pitch.pitch_data if isinstance(pitch.pitch_data, list) else [pitch.pitch_data])
            )
        ]
    
    claimed_pitches = Claim.objects.filter(user=user).order_by('claimed_at')
    
    context = {
        'current_page': current_page,
        'user_stats': user_stats,
        'claimed_pitches': claimed_pitches,
        'suggested_pitches': suggested_pitches,
        'user': user,
    }
    
    return render(request, 'dashboard/dashboard.html', context)

def get_user_stats(user):
    """
    Calculate user-specific statistics
    """
    # Get all claims
    claims = Claim.objects.filter(user=user)
    
    # Count verified claims
    verified_claims = claims.filter(status=Claim.VERIFIED).count()
    
    # List Pitches that have been claimed via Claim model
    user_pitches = Pitch.objects.filter(claims__user=user)
    
    # Calculate total engagement for user's pitches
    total_engagement = 0
    for pitch in user_pitches:
        engagement = pitch.get_engagement_data()
        total_engagement += engagement.get('likes', 0) + engagement.get('retweets', 0) + engagement.get('replies', 0)
    
    return {
        'total_owned': user_pitches.count(),
        'verified_claims': verified_claims,
        'total_engagement': total_engagement,
    }

@login_required
def onboard_user(request):
    """
    Handle user onboarding with X handle
    """
    if request.method == 'POST':
        x_handle = request.POST.get('x_handle', '').strip()
        
        if not x_handle:
            messages.error(request, "Please provide your X.com handle")
            return redirect('dashboard')
        
        # Remove @ if included
        if x_handle.startswith('@'):
            x_handle = x_handle[1:]
        
        # Update user profile
        profile, created = UserProfile.objects.get_or_create(user=request.user)
        profile.x_handle = x_handle
        profile.onboarding_complete = True
        profile.save()
        
        # Find pitches that mention this handle
        matching_pitches = []
        all_pitches = Pitch.objects.all()
        
        for pitch in all_pitches:
            if pitch.pitch_data:
                # Ensure pitch_data is a list
                pitch_data = pitch.pitch_data
                if isinstance(pitch_data, str):
                    try:
                        pitch_data = json.loads(pitch_data)
                    except json.JSONDecodeError:
                        pitch_data = []
                elif not isinstance(pitch_data, list):
                    pitch_data = []
                
                # Check if any mention matches the handle
                for mention in pitch_data:
                    if isinstance(mention, dict):
                        user_data = mention.get('user', {})
                        if user_data.get('handle', '').lower() == x_handle.lower():
                            # Create claim
                            Claim.objects.get_or_create(
                                user=request.user,
                                pitch=pitch,
                                defaults={'status': Claim.PENDING}
                            )
                            break
        
        messages.success(request, f"Found {len(matching_pitches)} pitches mentioning @{x_handle}")
        return redirect('dashboard')
    
    return redirect('dashboard')

@login_required
def claim_pitch(request):
    current_page = 'claim'
    context = {'current_page': current_page}
    if request.method == 'GET':
        name = request.GET.get('name')
        if name:
            claimable_pitches = Pitch.objects.filter(name__icontains=name)
            
            print(claimable_pitches.count())
            context['claimable_pitches'] = claimable_pitches
            messages.success(request, "🎉 Here are pitches you can claim.")
        else:
            messages.error(request, "Both fields are required.")
            # Optionally: context['product_url'] = product_url; context['name'] = name

        return render(request, 'dashboard/claim.html', context)
    return render(request, 'dashboard/claim.html', context)
# -------------------------------

# Fetch api function
@login_required
def verify_claim(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        pitch_id = data.get('pitch_id')
        role = data.get('role')
        verification_method = data.get('verification_method')

        if not all([pitch_id, role, verification_method]):
            return JsonResponse({'success': False, 'message': 'Missing required fields.'}, status=400)

        try:
            pitch = Pitch.objects.get(id=pitch_id)
            claim, created = Claim.objects.get_or_create(
                user=request.user, 
                pitch=pitch, 
                defaults={'status': Claim.PENDING, 'role': role, 'verification_method': verification_method}
            )

            if not created:
                return JsonResponse({'success': False, 'message': 'You have already submitted a claim for this pitch.'})
            
            return JsonResponse({'success': True, 'message': 'Pitch claimed successfully! We will review your claim.'})
        except Pitch.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Pitch not found.'}, status=404)
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'An error occurred: {str(e)}'}, status=500)

@login_required
@require_POST
def quick_claim(request):
    try:
        data = json.loads(request.body)
        pitch_id = data.get('pitch_id')

        if not pitch_id:
            return JsonResponse({'success': False, 'message': 'Pitch ID is required.'}, status=400)

        pitch = get_object_or_404(Pitch, id=pitch_id)

        claim, created = Claim.objects.get_or_create(
            user=request.user,
            pitch=pitch,
            defaults={'status': Claim.PENDING}
        )

        if not created:
            return JsonResponse({'success': False, 'message': 'You have already submitted a claim for this pitch.'})

        return JsonResponse({'success': True, 'message': 'Claim submitted! It is now pending verification.'})

    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)
