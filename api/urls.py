# urls.py
from django.urls import path
from . import views

urlpatterns = [
    # Web interface
    path('api-keys/', views.api_keys_list, name='api_keys_list'),
    path('api-keys/create/', views.create_api_key, name='create_api_key'),
    path('api-keys/<int:key_id>/delete/', views.delete_api_key, name='delete_api_key'),
    
    # API endpoints
    path('api/hello/', views.api_hello, name='api_hello'),
    path('api/user/', views.api_user_info, name='api_user_info'),
    path('api/data/', views.api_create_data, name='api_create_data'),
]
