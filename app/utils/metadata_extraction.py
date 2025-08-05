
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin


def get_meta_value(soup, keys):
    """
    Try to find a meta tag value using a list of (attribute, value) pairs.
    For example: [("property", "og:title"), ("name", "twitter:title")]
    Returns the first found content or None.
    """
    for attr, key in keys:
        tag = soup.find("meta", attrs={attr: key})
        if tag and tag.get("content"):
            return tag.get("content").strip()
    return None

def get_site_metadata(url):
    """Fetches the site and parses its metadata using BeautifulSoup."""
    
    try:
        print(f"Fetching metadata for URL: {url}")
        response = requests.get(url, timeout=5)
        print(f"Response status code: {response.status_code}")
    except requests.RequestException:
        print(f"Failed to fetch URL: {url}")
        return None

    soup = BeautifulSoup(response.text, 'html.parser')
    
    def ensure_absolute_url(base, url):
        # If the URL doesn't start with 'http', assume it's relative and join it with the base.
        if not url.startswith("http"):
            return urljoin(base, url)
        return url

    # In your metadata extraction function:
    metadata = {
        "title": get_meta_value(soup, [
                    ("property", "og:title"),
                    ("name", "twitter:title"),
                    ("name", "title")
                ]) or (soup.title.string.strip() if soup.title and soup.title.string else url),
        "description": get_meta_value(soup, [
                    ("property", "og:description"),
                    ("name", "description"),
                    ("name", "twitter:description")
                ]) or "",
        "image": ensure_absolute_url(url, get_meta_value(soup, [
                    ("property", "og:image"),
                    ("name", "twitter:image")
                ]) or ""),
        "url": get_meta_value(soup, [
                    ("property", "og:url"),
                    ("name", "twitter:url")
                ]) or url,
    }
    
    # Extract favicon
    icon_tag = soup.find("link", rel="icon") or soup.find("link", rel="shortcut icon")
    if icon_tag and icon_tag.get("href"):
        metadata["icon"] = urljoin(url, icon_tag["href"])
    else:
        metadata["icon"] = ""
    
    return metadata
