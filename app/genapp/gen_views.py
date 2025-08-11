from multiprocessing import context
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseBadRequest

from django.views.decorators.http import require_POST
from app.models import ReplyOpportunity, Pitch, Claim, GeneratedTweet
from app.genapp.generator import generate_pitch, article_generator, generate_article_titles #tweet_hook_generator  # your AI helper
import json


@login_required
def pitch_generator(request):
    user = request.user
    # All tweets admins imported
    reply_opportunities = ReplyOpportunity.objects.filter(content__isnull=False).order_by('-imported_at')
    # Only this user’s claimed pitches
    claimed_pitches = Pitch.objects.filter(claims__user=user).distinct()

    return render(request, 'dashboard/afterlaunch/pitch_generator.html', {
        'reply_opportunities': reply_opportunities,
        'claimed_pitches': claimed_pitches,
    })

@login_required
def generate_tweet_pitch(request):
    if request.method != 'POST':
        return HttpResponseBadRequest("Only POST allowed")

    try:
        data = json.loads(request.body)
        tweet_url = data['tweet_url']
        tweet_content   = data['tweet_content']
        pitch_id    = data['pitch_id']
        extra_ideas = data.get('extra_ideas', '')
    except (KeyError, ValueError):
        return HttpResponseBadRequest("Invalid payload")

    # Validate
    reply_to = get_object_or_404(ReplyOpportunity, url=tweet_url)
    pitch    = get_object_or_404(Pitch, id=pitch_id, claims__user=request.user)
    print(pitch)
    tool_details= f"""
                   Name: {pitch.name},
                   Title: {pitch.title},
                   Description: {pitch.description}
                   Content: {pitch.content}
                   Website Link: {pitch.url}
                   """
    # Build your AI prompt inside generate_pitch()
    try:
        pitch_reply = generate_pitch(
            tool_details = tool_details,  
            tweet_content = tweet_content, 
            extra_ideas = extra_ideas)
        print(pitch_reply)
    except Exception as e:
        import traceback
        print("Error in generate_pitch:", e)
        traceback.print_exc()
        return JsonResponse({'error': str(e)}, status=500)

    # Save it
    # GeneratedTweet.objects.create(
    #     user=request.user,
    #     pitch=pitch,
    #     reply_to=reply_to,
    #     content=pitch_reply
    # )

    return JsonResponse({'content': pitch_reply,'tweet_url': tweet_url,'tweet_content': tweet_content})

@login_required
def generate_titles(request):
    if request.method != 'POST':
        return JsonResponse({"error": "Only POST requests allowed"}, status=405)

    try:
        data = json.loads(request.body)
        pitch_id = data['pitch_id']
        extra_ideas = data.get('extra_ideas', '')
    except (KeyError, ValueError):
        return JsonResponse({"error": "Invalid data"}, status=400)

    try:
        # print(pitch_id, extra_ideas)        
        pitch    = get_object_or_404(Pitch, id=pitch_id)
        print(pitch)
        tool_details= f"""
                    Name: {pitch.name},
                    Title: {pitch.title},
                    Description: {pitch.description}
                    Content: {pitch.content}
                    Website Link: {pitch.url}
                    """
        titles = generate_article_titles(tool_details=tool_details, extra_ideas=extra_ideas)
        return JsonResponse({"titles": titles})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

@login_required
def generate_article(request):
    if request.method != 'POST':
        return JsonResponse({"error": "Only POST requests allowed"}, status=405)

    try:
        data = json.loads(request.body)
        pitch_id = data['pitch_id']
        extra_ideas = data.get('extra_ideas', '')
        title = data.get('title', '')
        title_description = data.get('title_description', '')
    except (KeyError, ValueError):
        return JsonResponse({"error": "Invalid data"}, status=400)

    pitch = get_object_or_404(Pitch, id=pitch_id, claims__user=request.user)

    tool_details = f"""
    Name: {pitch.name}
    Title: {pitch.title}
    Description: {pitch.description}
    Content: {pitch.content}
    Website: {pitch.url}
    """

    try:
        article = article_generator(tool_details=tool_details, extra_ideas=extra_ideas)
        return JsonResponse({"content": article})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

# article writer
def article_writer(request):
    user = request.user
    # Only this user’s claimed pitches
    claimed_pitches = Pitch.objects.filter(claims__user=user).distinct()
    new_pitches = Pitch.objects.filter().order_by('-created_at')[:4]
    context = {'user': user,'claimed_pitches': claimed_pitches,'new_pitches': new_pitches}
    return render(request, 'dashboard/afterlaunch/article.html', context)

# @login_required
# @require_POST
# def generate_tweet_hooks(request):
#     try:
#         data = json.loads(request.body)
#         pitch_id = data.get("pitch_id")
#         extra_ideas = data.get("extra_ideas", "")

#         if not pitch_id:
#             return JsonResponse({"error": "Missing pitch_id"}, status=400)

#         try:
#             pitch = Pitch.objects.get(id=pitch_id)
#             tool_details = f"""
#             Name: {pitch.name}
#             Title: {pitch.title}
#             Description: {pitch.description}
#             Content: {pitch.content}
#             Website: {pitch.url}
#             """
#         except Pitch.DoesNotExist:
#             return JsonResponse({"error": "Invalid pitch_id"}, status=404)

#         # Call the AI tweet hook generator
#         hooks_result = tweet_hook_generator(
#             tool_details=tool_details,
#             extra_ideas=extra_ideas
#         )

#         # If the AI call failed or returned an error
#         if isinstance(hooks_result, dict) and "error" in hooks_result:
#             return JsonResponse(hooks_result, status=500)

#         return JsonResponse({"hooks": hooks_result})

#     except Exception as e:
#         return JsonResponse({"error": str(e)}, status=500)


@login_required
def tweet_hook(request):
    user = request.user
    # Only this user’s claimed pitches
    claimed_pitches = Pitch.objects.filter(claims__user=user).distinct()
    new_pitches = Pitch.objects.filter().order_by('-created_at')[:4]
    context = {'user': user,'claimed_pitches': claimed_pitches,'new_pitches': new_pitches}
    return render(request, 'dashboard/afterlaunch/tweet.html', context)

