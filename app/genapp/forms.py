from django import forms
from app.models import Pitch, Claim, GeneratedTweet, GeneratedArticle


class PitchForm(forms.ModelForm):
    class Meta:
        model = Pitch
        fields = ['name', 'description', 'category']


class ClaimForm(forms.ModelForm):
    class Meta:
        model = Claim
        fields = ['pitch', 'user']

class GeneratedTweetForm(forms.ModelForm):
    class Meta:
        model = GeneratedTweet
        fields = ['pitch', 'author', 'content', 'category']
        widgets = {
            'pitch': forms.Select(attrs={'class': 'select is-fullwidth'}),
            'author': forms.HiddenInput(),  # since you assign author in view
            'content': forms.Textarea(attrs={'class': 'textarea'}),
            'category': forms.Select(attrs={'class': 'select is-fullwidth'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields['pitch'].queryset = Pitch.objects.filter(claims__user=user).distinct()


# class GeneratedArticleForm(forms.ModelForm):
#     class Meta:
#         model = GeneratedArticle
#         fields = ['pitch', 'user', 'title', 'content', 'tags', 'category', 'source', 'url', 'icon_url', 'banner_url', 'pitch_data', 'meta_data', 'seo_data', 'total_engagement', 'mention_count', 'clap', 'claimed', 'rank']
