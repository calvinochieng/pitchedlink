from django.urls import path
from . import gen_views

urlpatterns = [
    # …
    path('afterlaunch/pitch-generator/', gen_views.pitch_generator,      name='pitch_generator'),
    path('afterlaunch/generate-reply/',     gen_views.generate_tweet_pitch, name='generate_tweet_pitch'),
    path('afterlaunch/article-writer/',     gen_views.article_writer, name='article_writer'),
]
