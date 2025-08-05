# urls.py
from django.urls import path
from .pitch_management_views import  add_update_pitch

urlpatterns = [
    path('add/', add_update_pitch, name='add_update_pitch')
]