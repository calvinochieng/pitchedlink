# urls.py for the saas_analyzer app
from django.urls import path, include
from .views import *
from .dashboard_view import dashboard, onboard_user, claim_pitch,add_claim
from django.contrib.sitemaps.views import sitemap
from app.sitemaps import PitchSitemap, CategorySitemap, StaticViewSitemap

sitemaps = {
    'pitches': PitchSitemap,
    'categories': CategorySitemap,
    'static': StaticViewSitemap,
}

urlpatterns = [
    # Main pages
    path('', index, name='index'),
    path('pitches/', pitches, name='pitches'),
    path('home/', home, name='home'),
    path("leaderboard/", leaderboard, name="leaderboard"),
    path('categories/', categories, name='categories'),

    # Dashboard
    path('dashboard/', dashboard, name="dashboard"),
    path('dashboard/onboard/', onboard_user, name='onboard_user'),
    path('dashboard/claim_pitch/', claim_pitch, name='claim_pitch'),
    path('dashboard/add-claim/', add_claim, name='add_claim'),
    #Include genapp urls
    path('', include('app.genapp.gen_urls')),

    # General Pages
    path('about/', about, name='about'),
    path('contact/', contact, name='contact'),
    path('privacy-policy/', privacy_policy, name='privacy_policy'),
    path("refund-policy/", refund_policy, name="refund_policy"),
    path('terms-of-services/', terms_of_service, name='terms_of_service'),
    path('blog/', blog, name='blog'),
    path('pricing/', pricing, name="pricing"),

    # Sitemap
    path("sitemap.xml", sitemap, {"sitemaps": sitemaps}, name="sitemap"),

    # Pitch management
    path('', include('app.pitch_management_urls')),
    path('p/<slug:slug>/', detail, name='detail'),  
    path('clap_pitch/<slug:slug>/', clap_pitch, name='clap_pitch'),
    path('category/<slug:slug>/', category_detail, name='category_detail'),
    
]

