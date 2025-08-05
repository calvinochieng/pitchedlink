# views.py - Process everything in the view
import json
from datetime import datetime
from urllib.parse import urlparse
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from django.db import transaction
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils.text import slugify

from .models import Pitch, Category


def process_pitch_data(pitch_obj, pitch):
    # print("Show Pitch Data:", pitch)
    """
    Process and assign all data to the pitch object
    """
    # Store the raw JSON data
    pitch_obj.pitch_data = pitch.get('pitch_data', [])
    # print("Pitch Data From Process Pitch Data:", pitch.get('pitch_data', {}))
    pitch_obj.meta_data = pitch.get('meta_data', {})
    # print("Meta Data From Process Pitch Data:", pitch.get('meta_data', {}))
    pitch_obj.seo_data = pitch.get('seo_data', {})
    # print("SEO Data From Process Pitch Data:", pitch.get('seo_data', {}))
    
    # Process SEO data
    seo = pitch.get('seo_data', {})
    if seo:
        pitch_obj.name = seo.get('name') or seo.get('seo_title') or 'Untitled'
        pitch_obj.title = seo.get('seo_title', '')
        pitch_obj.description = seo.get('seo_description', '')
        pitch_obj.content = seo.get('seo_content', '')
        pitch_obj.tags = json.dumps(seo.get('tags', []))
        
        # Handle category
        category_id = seo.get('category_id')
        if category_id:
            try:
                pitch_obj.category = Category.objects.get(id=category_id)
            except Category.DoesNotExist:
                print(f"Category with id {category_id} not found")
    
    # Process meta data
    meta = pitch.get('meta_data', {})
    if meta:
        pitch_obj.url = meta.get('final_url', '')
        pitch_obj.icon_url = meta.get('icon_url', '')
        pitch_obj.banner_url = meta.get('banner_url', '')
        
        # Handle social links
        social_links = meta.get('social_links', {})
        pitch_obj.social_links = json.dumps(social_links)
    
    data_pitch = pitch.get('pitch_data', [])
    # print("Pitch Data:", data_pitch)
    if data_pitch:
        # print("Reply Link:", data_pitch[-1].get('replyLink', ''))
        print("Reply Link:", data_pitch[-1].get('replyLink', ''))

        pitch_obj.source = data_pitch[-1].get('replyLink', '')

    
    # Generate slug if needed
    if not pitch_obj.slug and pitch_obj.name:
        pitch_obj.slug = slugify(pitch_obj.name)
        original_slug = pitch_obj.slug
        num = 1
        while Pitch.objects.filter(slug=pitch_obj.slug).exclude(pk=pitch_obj.pk).exists():
            pitch_obj.slug = f"{original_slug}-{num}"
            num += 1


@login_required
def add_update_pitch(request):
    """
    View to add or update pitches based on URL - Process everything here
    """
    error = None
    created_count = 0
    updated_count = 0
    created_pitches = []
    updated_pitches = []
    
    if request.method == "POST":
        pitch_json = request.POST.get("pitch_json", "")
        
        try:
            # Parse the incoming data
            pitches = json.loads(pitch_json)
            if not isinstance(pitches, list):
                raise ValueError("Expected a list of pitch objects.")
                
            with transaction.atomic():
                # Process each pitch
                for pitch in pitches:
                    # Get URL from meta_data
                    url = pitch.get('meta_data', {}).get('final_url')
                    
                    if not url:
                        print("Skipping pitch: No URL found")
                        continue
                        
                    # print(f"Processing URL: {url}")
                    # print("Meta Data:", pitch_data.get('meta_data', {})) 
                    # print("SEO Data:", pitch_data.get('seo_data', {}))
                    
                    # Try to get existing pitch by URL
                    existing_pitch = Pitch.objects.filter(url=url).first()
                    
                    if existing_pitch:
                        # print(f"Updating existing pitch: {existing_pitch.name}")
                        
                        # Handle pitch_data updates (merge new with existing)
                        new_pitch_data = pitch.get('pitch_data', {})
                        # print("New Pitch Data:", new_pitch_data)
                        # print("New Pitch Data Type:", type(new_pitch_data))
                        
                        # Ensure existing_pitch_data is a list
                        existing_pitch_data = existing_pitch.pitch_data
                        if isinstance(existing_pitch_data, str):
                            try:
                                existing_pitch_data = json.loads(existing_pitch_data)
                            except json.JSONDecodeError:
                                existing_pitch_data = []
                        elif not isinstance(existing_pitch_data, list):
                            existing_pitch_data = []
                        
                        # print(f"Existing pitch data type: {type(existing_pitch_data)}")
                        # print(f"Existing pitch data length: {len(existing_pitch_data) if existing_pitch_data else 0}")
                        
                        # Update or append each new pitch
                        new_reply_link = new_pitch_data.get('replyLink','')
                        # print("New Reply Link:", new_reply_link)
                        if existing_pitch_data:
                            for pitch_data in existing_pitch_data:
                                print("Pitch Data From For Loop:", pitch_data)                               
                                # Find existing pitch with same replyLink
                                existing_index = None
                                for i, p in enumerate(existing_pitch_data):
                                    if isinstance(p, dict) and p.get('replyLink') == new_reply_link:
                                        existing_index = i
                                        break
                            
                            if existing_index is not None:
                                # Update existing pitch data
                                existing_pitch_data[existing_index] = new_pitch_data
                                print(f"Updated existing pitch data at index {existing_index}")
                            else:
                                # Append new pitch data
                                existing_pitch_data.append(new_pitch_data)
                                print("Added new pitch data", existing_pitch_data)
                        else:
                            existing_pitch_data.append(new_pitch_data)
                        
                        # Update the pitch_data and process all data
                        pitch['pitch_data'] = existing_pitch_data
                        process_pitch_data(existing_pitch, pitch)
                        
                        # Save the updated pitch
                        existing_pitch.save()
                        updated_count += 1
                        updated_pitches.append(existing_pitch)
                        
                    else:
                        print("Creating new pitch")
                        
                        # Create new pitch
                        new_pitch = Pitch(user=request.user)
                        
                        # Process all the 
                        
                        pitch['pitch_data'] = [pitch.get('pitch_data', {})]
                        # pitch.pitch_data = pitch.get('pitch_data', {})
                        # print("Pitch Data From Add Update Pitch:", pitch.get('pitch_data', {}))
                        # print("TYPE OF PITCH DATA", type(pitch['pitch_data']))
                        print("PITCH DATA", pitch['pitch_data'])
                        process_pitch_data(new_pitch, pitch)
                        
                        # Ensure we have required fields
                        if not new_pitch.name:
                            new_pitch.name = f"Pitch from {urlparse(url).netloc}"
                        
                        # Save the new pitch
                        new_pitch.save()
                        created_count += 1
                        created_pitches.append(new_pitch)
                        print(f"Created new pitch: {new_pitch.name}")
                        
        except json.JSONDecodeError as e:
            error = f"Invalid JSON data: {str(e)}"
            messages.error(request, error)
            print(f"JSON Error: {e}")
            
        except ValueError as e:
            error = f"Data validation error: {str(e)}"
            messages.error(request, error)
            print(f"Validation Error: {e}")
            
        except Exception as e:
            error = f"Error processing pitches: {str(e)}"
            messages.error(request, error)
            print(f"General Error: {e}")
            import traceback
            traceback.print_exc()
            
    # Show success messages
    if created_count > 0:
        messages.success(request, f"Successfully created {created_count} new pitch{'es' if created_count > 1 else ''}")
        print(f"Created {created_count} pitches")
    
    if updated_count > 0:
        messages.success(request, f"Successfully updated {updated_count} existing pitch{'es' if updated_count > 1 else ''}")
        print(f"Updated {updated_count} pitches")
    
    if created_count == 0 and updated_count == 0 and request.method == "POST":
        messages.info(request, "No new or updated pitches were processed")
    
    return render(request, "pitches/management/pitch_list_view.html", {
        "error": error,
        "created_count": created_count,
        "updated_count": updated_count,
        "created_pitches": created_pitches,
        "updated_pitches": updated_pitches,
    })