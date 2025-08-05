# sitemaps.py
from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from .models import Pitch, Category

class PitchSitemap(Sitemap):
    changefreq = "daily"
    priority = 0.9
    protocol = "https"

    def items(self):
        # Only show launched pitches
        return Pitch.objects.all()

    def lastmod(self, obj):
        return obj.updated_at

    def location(self, obj):
        return f"/p/{obj.slug}/"

class CategorySitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.6
    protocol = "https"

    def items(self):
        return Category.objects.filter(is_active=True)

    def location(self, obj):
        return f"/category/{obj.slug}/"


class StaticViewSitemap(Sitemap):
    changefreq = "monthly"
    priority = 0.5
    protocol = "https"

    def items(self):
        return [
            "home",         # path("", views.home, name="home")
            "about",        # path("about/", views.about, name="about")
            "contact",      # path("contact/", views.contact, name="contact")
            # Add more as needed
        ]

    def location(self, item):
        return reverse(item)

