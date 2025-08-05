
# models.py
import secrets
import hashlib
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class APIKey(models.Model):
    name = models.CharField(max_length=100)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='api_keys')
    key_hash = models.CharField(max_length=64, unique=True)
    prefix = models.CharField(max_length=8)
    suffix = models.CharField(max_length=4, null=True)  # Last 4 characters for display
    created_at = models.DateTimeField(auto_now_add=True)
    last_used = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'api_keys'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} ({self.prefix}...{self.suffix})"
    
    @property
    def display_key(self):
        """Return a display version of the key"""
        return f"{self.prefix}{'*' * 20}...{self.suffix}"
    
    @classmethod
    def generate_key(cls, user, name):
        """Generate a new API key"""
        raw_key = secrets.token_urlsafe(32)
        prefix = raw_key[:8]
        suffix = raw_key[-4:]  # Last 4 characters
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        
        api_key = cls.objects.create(
            user=user,
            name=name,
            key_hash=key_hash,
            prefix=prefix,
            suffix=suffix
        )
        
        return api_key, raw_key
    
    @classmethod
    def authenticate(cls, raw_key):
        """Validate an API key"""
        if not raw_key:
            return None
            
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        
        try:
            api_key = cls.objects.get(key_hash=key_hash, is_active=True)
            # Update last used
            api_key.last_used = timezone.now()
            api_key.save(update_fields=['last_used'])
            return api_key
        except cls.DoesNotExist:
            return None






