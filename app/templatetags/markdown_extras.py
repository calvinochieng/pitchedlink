from django import template
from django.utils.safestring import mark_safe
import markdown

register = template.Library()

@register.filter(name='markdown')
def markdown_format(text):
    """
    Convert markdown text to HTML
    """
    if not text:
        return ''
    
    # Configure markdown with useful extensions
    md = markdown.Markdown(extensions=[
        'markdown.extensions.extra',      # Tables, footnotes, etc.
        'markdown.extensions.codehilite', # Syntax highlighting
        'markdown.extensions.toc',        # Table of contents
        'markdown.extensions.nl2br',      # Convert newlines to <br>
    ])
    
    html = md.convert(text)
    return mark_safe(html)