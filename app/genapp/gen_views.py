from multiprocessing import context
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseBadRequest
from app.models import ReplyOpportunity, Pitch, Claim, GeneratedTweet
from app.genapp.generator import generate_pitch  # your AI helper
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

# article writer
def article_writer(request):
    user = request.user
    # Only this user’s claimed pitches
    claimed_pitches = Pitch.objects.filter(claims__user=user).distinct()
    context = {'user': user,'claimed_pitches': claimed_pitches}
    return render(request, 'dashboard/afterlaunch/article.html', context)


