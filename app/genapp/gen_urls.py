from django.urls import path
from . import gen_views

urlpatterns = [
    # …
    path('afterlaunch/pitch-generator/', gen_views.pitch_generator,      name='pitch_generator'),
    path('afterlaunch/generate-reply/',     gen_views.generate_tweet_pitch, name='generate_tweet_pitch'),
    path('afterlaunch/generate-article/',     gen_views.generate_article, name='generate_article'),
    path('afterlaunch/generate-titles/',     gen_views.generate_titles, name='generate_titles'),
    path('afterlaunch/article-writer/',     gen_views.article_writer, name='article_writer'),
    
#     path('afterlaunch/generate_tweet_hooks/', gen_views.generate_tweet_hooks, name='generate_tweet_hooks'),
    path('afterlaunch/tweet_hook/', gen_views.tweet_hook, name='tweet_hook'),
 ]
