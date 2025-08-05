# models.py
import json
from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify
from django.utils import timezone
from bs4 import BeautifulSoup
from .utils.ranking_system import calculate_rank

from django.core.exceptions import ValidationError
import re

class Category(models.Model):
    """Categories for organizing pitches"""
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField(blank=True, null=True)
    color = models.CharField(max_length=7, default="#3B82F6", help_text="Hex color code for category display")
    icon = models.CharField(max_length=50, blank=True, null=True, help_text="Icon class or name")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['name']
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
            original_slug = self.slug
            num = 1
            while Category.objects.filter(slug=self.slug).exclude(pk=self.pk).exists():
                self.slug = f"{original_slug}-{num}"
                num += 1
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.name

class Pitch(models.Model):
    # Existing fields
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='pitches', null=True, blank=True)

    # Icon and banner urls from metadata
    icon_url = models.URLField(blank=True, null=True) # Icon from meta_data icon_url
    banner_url = models.URLField(blank=True, null=True) # Banner from meta_data banner_url   
    url = models.URLField(blank=True, null=True) # URL of the source page from metadata final_url

    # Site content section
    name = models.CharField(max_length=255) # Name from seo_data
    title = models.CharField(max_length=255) # Title from seo_data title
    description = models.TextField(blank=True, null=True) # Description from seo_data description
    content = models.TextField(blank=True, null=True) # Content from seo_data content
    social_links = models.CharField(max_length=255) # Social links from meta_data social_links
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='pitches') # Category from seo_data category_id
    tags = models.CharField(max_length=255) # Tags from seo_data tags
    slug = models.SlugField(unique=True, blank=True)
    # SEO data
    seo_data = models.JSONField(default=dict, blank=True, null=True, help_text="SEO-related data including title, description, and tags")
    
 

    # Social media pitch data
    pitch_data = models.JSONField(default=list, blank=True, null=True, help_text="Social media post data including user info, engagement, and content")
    meta_data = models.JSONField(default=dict, blank=True, null=True, help_text="Metadata including URLs and social links")
    source = models.URLField(blank=True, null=True)  # URL of the source page ie social media thread
    
    
    # Basic fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_featured = models.BooleanField(default=False)
    is_launched = models.BooleanField(default=False)
    launch_date = models.DateTimeField(default=timezone.now)
    
    # Stats and Ranking Section
    total_engagement = models.JSONField(default=dict, blank=True, null=True, help_text="Aggregated engagement metrics from all social media mentions")
    mention_count = models.IntegerField(default=0, help_text="Number of social media mentions")
    # Clap field now managed by the Clap model
    clap = models.IntegerField(default=0, help_text="Total effective claps from all users")
    claimed = models.BooleanField(default=False)
    rank = models.IntegerField(default=1)
    
    def add_clap(self, user):
        """Add a clap from a user to this pitch"""
        clap, created = Clap.objects.get_or_create(
            user=user,
            pitch=self,
            defaults={'count': 1}
        )
        
        if not created:
            # If user already clapped, increment their clap count
            clap.add_clap()
        
        # Update the total effective claps
        self.clap = self.get_effective_clap_count()
        self.save(update_fields=['clap'])
        return self.clap
    
    def get_clap_count(self):
        """Get the total number of claps for this pitch"""
        return self.user_claps.aggregate(total_claps=models.Sum('count'))['total_claps'] or 0
    
    def get_effective_clap_count(self):
        """Get the total effective number of claps for this pitch"""
        return sum(clap.get_effective_claps() for clap in self.user_claps.all())
    
    def has_user_clapped(self, user):
        """Check if a user has clapped for this pitch"""
        if not user.is_authenticated:
            return False
        return self.user_claps.filter(user=user).exists()
    
    def get_user_clap_count(self, user):
        """Get the number of times a user has clapped for this pitch"""
        if not user.is_authenticated:
            return 0
        try:
            return self.user_claps.get(user=user).count
        except Clap.DoesNotExist:
            return 0
    
    class Meta:
        ordering = ['-rank', '-created_at']
        indexes = [
            models.Index(fields=['rank']),
            models.Index(fields=['category']),
            models.Index(fields=['is_featured']),
            models.Index(fields=['created_at']),
        ]
    
    def get_engagement_data(self):
            """Calculate total engagement from all pitch_data entries"""
            if not self.pitch_data:
                return {"replies": 0, "retweets": 0, "likes": 0, "views": 0}
            
            # Ensure pitch_data is a list
            pitch_data = self.pitch_data
            if isinstance(pitch_data, str):
                try:
                    pitch_data = json.loads(pitch_data)
                except json.JSONDecodeError:
                    pitch_data = []
            elif not isinstance(pitch_data, list):
                pitch_data = []
            
            total = {"replies": 0, "retweets": 0, "likes": 0, "views": 0}
            for pitch in pitch_data:
                if isinstance(pitch, dict):
                    engagement = pitch.get("engagement", {})
                    for key in total:
                        total[key] += engagement.get(key, 0)
            
            return total
    
    def rank_setter(self):
        """
        Calculate the ranking score using ALL engagement metrics from pitch_data,
        the number of claps, and claimed status.
        """
        # Calculate total engagement from all social media mentions
        total_engagement = self.get_engagement_data()
        
        # Update the stored total_engagement field
        self.total_engagement = total_engagement
        
        # Get mention count safely
        pitch_data = self.pitch_data
        if isinstance(pitch_data, str):
            try:
                pitch_data = json.loads(pitch_data)
            except json.JSONDecodeError:
                pitch_data = []
        elif not isinstance(pitch_data, list):
            pitch_data = []
            
        self.mention_count = len(pitch_data)
        
        # Calculate rank using total engagement
        score = calculate_rank(
            engagement_data=total_engagement,
            claps=self.clap,
            claimed=self.claimed
        )
        self.rank = score
        
    def get_engagement_score(self):
        """Get a simple engagement score for display"""
        if not self.total_engagement:
            return 0
        
        total = self.total_engagement
        return (total.get('likes', 0) + 
                total.get('retweets', 0) * 2 + 
                total.get('replies', 0) * 3)

    def save(self, *args, **kwargs):
        # Update rank and engagement totals
        self.rank_setter()
        
        # Generate slug if not exists
        if not self.slug and self.name:
            self.slug = slugify(self.name)
            original_slug = self.slug
            num = 1
            while Pitch.objects.filter(slug=self.slug).exclude(pk=self.pk).exists():
                self.slug = f"{original_slug}-{num}"
                num += 1
        
        # Ensure we have a name
        if not self.name:
            self.name = "Untitled Pitch"
        
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.category.name if self.category else 'Uncategorized'})"
    
    def get_latest_mention(self):
        """Get the most recent social media mention"""
        if not self.pitch_data:
            return None
        
        # Ensure pitch_data is a list
        pitch_data = self.pitch_data
        if isinstance(pitch_data, str):
            try:
                pitch_data = json.loads(pitch_data)
            except json.JSONDecodeError:
                pitch_data = []
        elif not isinstance(pitch_data, list):
            pitch_data = []
        
        if not pitch_data:
            return None
        
        # Sort by timestamp and return the latest
        sorted_pitches = sorted(
            [p for p in pitch_data if isinstance(p, dict)], 
            key=lambda x: x.get('timestamp', {}).get('datetime', ''), 
            reverse=True
        )
        return sorted_pitches[0] if sorted_pitches else None
    
    # def rank_setter(self):
    #     """
    #     Calculate the ranking score using ALL engagement metrics from pitch_data,
    #     the number of claps, and claimed status.
    #     """
    #     # Calculate total engagement from all social media mentions
    #     total_engagement = self.get_engagement_data()
        
    #     # Update the stored total_engagement field
    #     self.total_engagement = total_engagement
    #     self.mention_count = len(self.pitch_data) if self.pitch_data else 0
        
    #     # Calculate rank using total engagement
    #     score = calculate_rank(
    #         engagement_data=total_engagement,
    #         claps=self.clap,
    #         claimed=self.claimed
    #     )
    #     self.rank = score
        
    # def get_engagement_score(self):
    #     """Get a simple engagement score for display"""
    #     if not self.total_engagement:
    #         return 0
        
    #     total = self.total_engagement
    #     return (total.get('likes', 0) + 
    #             total.get('retweets', 0) * 2 + 
    #             total.get('replies', 0) * 3)

    # def save(self, *args, **kwargs):
    #     # Update rank and engagement totals
    #     self.rank_setter()
        
    #     # Generate slug if not exists
    #     if not self.slug and self.name:
    #         self.slug = slugify(self.name)
    #         original_slug = self.slug
    #         num = 1
    #         while Pitch.objects.filter(slug=self.slug).exclude(pk=self.pk).exists():
    #             self.slug = f"{original_slug}-{num}"
    #             num += 1
        
    #     # Ensure we have a name
    #     if not self.name:
    #         self.name = "Untitled Pitch"
        
    #     return None# super().save(*args, **kwargs)

    # def __str__(self):
    #     return f"{self.name} ({self.category.name if self.category else 'Uncategorized'})"
    
    # def get_latest_mention(self):
        """Get the most recent social media mention"""
        if not self.pitch_data:
            return None
        
        # Sort by timestamp and return the latest
        sorted_pitches = sorted(
            self.pitch_data, 
            key=lambda x: x.get('timestamp', {}).get('datetime', ''), 
            reverse=True
        )
        return sorted_pitches[0] if sorted_pitches else None   
    
    
class PitchAnalytics(models.Model):
    """Store analytics and tracking data for pitches"""
    pitch = models.OneToOneField(Pitch, on_delete=models.CASCADE, related_name='analytics')
    
    # View statistics
    views_today = models.IntegerField(default=0)
    views_week = models.IntegerField(default=0)
    views_month = models.IntegerField(default=0)
    views_total = models.IntegerField(default=0)
    
    # Click statistics
    clicks_today = models.IntegerField(default=0)
    clicks_week = models.IntegerField(default=0)  
    clicks_month = models.IntegerField(default=0)
    clicks_total = models.IntegerField(default=0)
    
    # Social media growth
    social_mentions_growth = models.JSONField(default=dict, blank=True, null=True)
    engagement_growth = models.JSONField(default=dict, blank=True, null=True)
    
    # Timestamps
    last_view = models.DateTimeField(null=True, blank=True)
    last_click = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Analytics for {self.pitch.name}"


# models.py
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    x_handle = models.CharField(max_length=50, blank=True, null=True)
    onboarding_complete = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username} - @{self.x_handle}"

class Clap(models.Model):
    """
    Tracks individual claps from users on pitches with the following logic:
    - 1st clap = 1 clap
    - Next 5 claps = 1 clap (total 2 claps after 6 claps)
    - Next 4 claps = 1 clap (total 3 claps after 10 claps)
    - Further claps don't increment the count
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='claps')
    pitch = models.ForeignKey('Pitch', on_delete=models.CASCADE, related_name='user_claps')
    count = models.PositiveIntegerField(default=1)
    last_clapped = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'pitch')
        ordering = ['-last_clapped']
        indexes = [
            models.Index(fields=['pitch', 'user']),
            models.Index(fields=['pitch', '-last_clapped']),
        ]

    def __str__(self):
        return f"{self.user.username} clapped {self.count} times on {self.pitch.name}"



    def get_effective_claps(self):
        """Calculate the effective number of claps based on the clapping rules"""
        if self.count <= 1:
            return self.count
        elif self.count <= 6:  # 1 (first) + 5 = 6 claps
            return 2
        elif self.count <= 10:  # 6 (previous) + 4 = 10 claps
            return 3
        return 3  # Max 3 claps per user per pitch

    def add_clap(self):
        """Increment the clap count if allowed"""
        if self.count < 10:  # Only increment if under the max
            self.count += 1
            self.save()
        return self.count


class Claim(models.Model):
    PENDING = 'pending'
    VERIFIED = 'verified'
    REJECTED = 'rejected'
    STATUS_CHOICES = [
        (PENDING, 'Pending Verification'),
        (VERIFIED, 'Verified'),
        (REJECTED, 'Rejected'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='claims')
    pitch = models.ForeignKey(Pitch, on_delete=models.CASCADE, related_name='claims')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=VERIFIED)
    claimed_at = models.DateTimeField(auto_now_add=True)
    verified_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s claim on {self.pitch.name}"

    class Meta:
        unique_together = ('user', 'pitch')
        ordering = ['-claimed_at']

# ------AFTERLAUNCH------#


# ------TWEET URL POSTER ------#
class TweetBatch(models.Model):
    """
    Admins paste raw Tweet URLs here (one per line). On save, each line
    becomes its own ReplyOpportunity.
    """
    name = models.CharField(max_length=100, help_text="A label for this batch import")
    raw_urls = models.TextField(
        help_text="Paste one Tweet URL per line. On save, each valid URL will be imported."
    )
    created_at = models.DateTimeField(default=timezone.now)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Parse and import each URL
        from .models import ReplyOpportunity
        for line in self.raw_urls.splitlines():
            url = line.strip()
            if not url:
                continue
            # Basic validation
            if url.startswith("http") and "/status/" in url:
                # Create if not exists
                ReplyOpportunity.objects.get_or_create(url=url)

    def __str__(self):
        return f"{self.name} ({self.created_at:%Y-%m-%d})"


class ReplyOpportunity(models.Model):
    """
    A single tweet URL that users can choose to reply to.
    Prevents duplicate tweet IDs from being posted.
    """
    url = models.URLField(unique=True)
    tweet_id = models.CharField(max_length=50, unique=True, editable=False, blank=True, null=True)
    content = models.TextField(blank=True, null=True)
    embeded = models.TextField(blank=True, null=True)
    imported_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        # Extract tweet ID from the URL
        match = re.search(r'x\.com/.+/status/(\d+)', self.url)
        if not match:
            raise ValidationError("Invalid tweet URL. Cannot extract tweet ID.")
        self.tweet_id = match.group(1)

        # Check if a tweet with this ID already exists
        if ReplyOpportunity.objects.exclude(pk=self.pk).filter(tweet_id=self.tweet_id).exists():
            raise ValidationError("This tweet has already been added.")

    def save(self, *args, **kwargs):
        self.clean()  # Ensures validation even when save() is called directly

        if self.embeded and not self.content:
            soup = BeautifulSoup(self.embeded, 'html.parser')
            tweet_paragraph = soup.find('p')
            if tweet_paragraph:
                self.content = tweet_paragraph.get_text(separator='\n', strip=True)

        super().save(*args, **kwargs)

    def __str__(self):
        return self.content if self.content else self.url
#---------- Generative Models ------------#

class GeneratedArticle(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    pitch= models.ForeignKey(Pitch, on_delete=models.CASCADE)
    title = models.CharField(max_length=200, blank=True)
    image = models.ImageField(upload_to='generated_content', blank=True, null=True)
    description = models.TextField()
    content = models.TextField()
    category = models.CharField(max_length=100, blank=True)
    tags = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    slug = models.SlugField(unique=True, blank=True, null=True)

    def __str__(self):
        return f"{self.author.username} - {self.pitch.name}"
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
            original_slug = self.slug
            num = 1
            while GeneratedArticle.objects.filter(slug=self.slug).exclude(pk=self.pk).exists():
                self.slug = f"{original_slug}-{num}"
                num += 1
        super().save(*args, **kwargs)

class GeneratedTweet(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    pitch = models.ForeignKey(Pitch, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    category = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f"{self.author.username} - {self.pitch.name}: Tweet - {self.content}"