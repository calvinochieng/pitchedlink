
# def get_domain_from_url(url):
#     """Extract domain from URL"""
#     try:
#         parsed = urlparse(url)
#         domain = parsed.netloc.lower()
#         # Remove www. prefix if present
#         if domain.startswith('www.'):
#             domain = domain[4:]
#         return domain
#     except:
#         return None

import requests
from urllib.parse import urlparse

# Blacklist of promotional/launch domains and patterns
PROMOTIONAL_DOMAINS = {
    'producthunt.com', 'betalist.com', 'launchingnext.com', 'startuptracker.io',
    'indiehackers.com', 'hackernews.com', 'reddit.com', 'twitter.com', 
    'linkedin.com', 'facebook.com', 'instagram.com', 'tiktok.com',
    'kickstarter.com', 'indiegogo.com', 'gofundme.com', 
    'medium.com', 'substack.com', 'dev.to', 'hashnode.com',
    'angel.co', 'crunchbase.com', 'f6s.com', 'startupgrind.com',
    'betapage.co', 'startupstash.com', 'alternative.me', 'saashub.com',
    'capterra.com', 'g2.com', 'trustpilot.com', 'appsumo.com',
    'youtube.com', 'youtu.be', 'vimeo.com', 'twitch.tv',
    'slideshare.net', 'scribd.com', 'issuu.com', 'github.com',
    'gitlab.com', 'bitbucket.org', 'sourceforge.net', 'codepen.io',
}

# URL patterns that indicate promotional content
PROMOTIONAL_PATTERNS = [
    '/posts/', '/post/', '/launch/', '/startup/', '/product/', '/app/',
    '/review/', '/listing/', '/profile/', '/company/', '/campaign/',
    '/project/', '/pitch/', '/demo/', '/beta/', '/early-access/',
    '/coming-soon/', '/signup/', '/waitlist/', '/preorder/'
]

def is_promotional_url(url, domain=None):
    """
    Check if URL is from a promotional/launch platform or contains promotional patterns.
    """
    try:
        parsed = urlparse(url)
        check_domain = domain or parsed.netloc.lower()
        
        # Remove www. prefix for checking
        if check_domain.startswith('www.'):
            check_domain = check_domain[4:]
        
        # Check if domain is in blacklist
        if check_domain in PROMOTIONAL_DOMAINS:
            return True
        
        # Check URL path for promotional patterns
        path = parsed.path.lower()
        if any(pattern in path for pattern in PROMOTIONAL_PATTERNS):
            return True
            
        # Check for common promotional subdomains
        if any(subdomain in check_domain for subdomain in ['launch.', 'beta.', 'promo.', 'campaign.']):
            return True
            
        return False
    except:
        return False

def get_final_url(url, max_redirects=10):
    """
    Follow redirects to get the final URL.
    Returns the final URL after following all redirects, or original URL if blocked/failed.
    """
    try:
        # Use HEAD request first (faster, only gets headers)
        response = requests.head(url, allow_redirects=True, timeout=10, 
                               headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})
        
        # Check if we got blocked by Cloudflare or similar
        if is_blocked_response(response):
            print(f"Access blocked for {url} (Status: {response.status_code})")
            return url
            
        return response.url
    except requests.exceptions.RequestException as e:
        try:
            # Fallback to GET request if HEAD fails
            response = requests.get(url, allow_redirects=True, timeout=10,
                                  headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})
            
            # Check if we got blocked by Cloudflare or similar
            if is_blocked_response(response):
                print(f"Access blocked for {url} (Status: {response.status_code})")
                return url
                
            return response.url
        except requests.exceptions.RequestException as e2:
            print(f"Failed to access {url}: {e2}")
            # If both fail, return original URL
            return url

def is_blocked_response(response):
    """
    Check if the response indicates we're being blocked by Cloudflare or similar services.
    """
    # Common status codes for blocks
    blocked_status_codes = [403, 429, 503, 520, 521, 522, 523, 524, 525, 526, 527, 530]
    
    if response.status_code in blocked_status_codes:
        return True
    
    # Check for Cloudflare specific indicators in response text (if available)
    try:
        content = response.text.lower() if hasattr(response, 'text') else ""
        cloudflare_indicators = [
            'cloudflare', 'ray id', 'cf-ray', 'attention required',
            'checking your browser', 'ddos protection', 'security check',
            'challenge page', 'just a moment'
        ]
        
        if any(indicator in content for indicator in cloudflare_indicators):
            return True
    except:
        # If we can't check content, just rely on status code
        pass
    
    return False

def get_domain_from_url(url):
    """
    Extract domain from URL, following redirects if it's a shortened URL.
    Returns None for promotional/blacklisted URLs.
    """
    try:
        # First check if it's a promotional URL - if so, return None
        if is_promotional_url(url):
            print(f"Promotional URL detected, skipping: {url}")
            return None
        
        # Check if it's a known URL shortener
        parsed = urlparse(url)
        shorteners = ['t.co', 'bit.ly', 'tinyurl.com', 'goo.gl', 'ow.ly', 
                     'short.link', 'rb.gy', 'is.gd', 'buff.ly', 'soo.gd']
        
        current_domain = parsed.netloc.lower()
        if current_domain.startswith('www.'):
            current_domain = current_domain[4:]
            
        # If it's a URL shortener, follow redirects to get final URL
        if current_domain in shorteners:
            final_url = get_final_url(url)
            
            # Check if the final URL is promotional
            if is_promotional_url(final_url):
                print(f"Final URL is promotional, skipping: {final_url}")
                return None
                
            parsed = urlparse(final_url)
        
        domain = parsed.netloc.lower()
        print(f"Extracted domain: {domain} from URL: {url}")
        # Remove www. prefix if present
        if domain.startswith('www.'):
            domain = domain[4:]
            print(f"Domain extracted: {domain} from URL: {url}")
        return domain
    except Exception as e:
        print(f"Error processing URL {url}: {e}")
        return None

# Alternative version that always checks for redirects
def get_domain_from_url_always_check(url):
    """
    Extract domain from URL, always following redirects first.
    Returns None for promotional/blacklisted URLs.
    """
    try:
        # First check if it's a promotional URL - if so, return None
        if is_promotional_url(url):
            print(f"Promotional URL detected, skipping: {url}")
            return None
            
        # Always get the final URL first
        final_url = get_final_url(url)
        
        # Check if the final URL is promotional
        if is_promotional_url(final_url):
            print(f"Final URL is promotional, skipping: {final_url}")
            return None
            
        parsed = urlparse(final_url)
        
        domain = parsed.netloc.lower()
        # Remove www. prefix if present
        if domain.startswith('www.'):
            domain = domain[4:]
        return domain
    except Exception as e:
        print(f"Error processing URL {url}: {e}")
        return None

# Function to add custom domains to blacklist
def add_promotional_domain(domain):
    """Add a custom domain to the promotional blacklist."""
    clean_domain = domain.lower()
    if clean_domain.startswith('www.'):
        clean_domain = clean_domain[4:]
    PROMOTIONAL_DOMAINS.add(clean_domain)
    print(f"Added {clean_domain} to promotional blacklist")

# Function to check if a domain is blacklisted
def is_domain_blacklisted(domain):
    """Check if a domain is in the promotional blacklist."""
    clean_domain = domain.lower()
    if clean_domain.startswith('www.'):
        clean_domain = clean_domain[4:]
    return clean_domain in PROMOTIONAL_DOMAINS

# Example usage with promotional URL blacklisting:
if __name__ == "__main__":
    # Test URLs including promotional ones
    test_urls = [
        "https://t.co/waIBbCaqxz",  # Shortened URL
        "https://www.google.com",   # Normal URL
        "https://producthunt.com/posts/awesome-app",  # Promotional URL
        "https://bit.ly/3example",  # Another shortener
        "https://github.com/user/repo",  # Normal URL
        "https://www.reddit.com/r/startup/posts/123",  # Social media promo
        "https://angel.co/company/startup-name",  # Investment platform
        "https://medium.com/@user/my-app-launch-456",  # Blog promo
        "https://httpstat.us/403",  # Test blocked response
    ]
    
    print("Testing get_domain_from_url (with promotional blacklist):")
    for url in test_urls:
        domain = get_domain_from_url(url)
        print(f"{url} -> {domain}")
    
    print("\n" + "="*50)
    print("Testing custom blacklist addition:")
    add_promotional_domain("custompromo.com")
    test_custom = "https://custompromo.com/launch/myapp"
    domain = get_domain_from_url(test_custom)
    print(f"{test_custom} -> {domain}")
    
    print("\n" + "="*50)
    print("Testing domain blacklist check:")
    domains_to_check = ["producthunt.com", "google.com", "reddit.com"]
    for domain in domains_to_check:
        is_blacklisted = is_domain_blacklisted(domain)
        print(f"{domain} -> Blacklisted: {is_blacklisted}")