from urllib.parse import urlparse, urljoin
from flask import request


def is_safe_redirect_url(target: str) -> bool:
    """Only allow redirecting to a `next` URL that points back at this same host,
    so a crafted login link can't bounce a user off to an attacker's site."""
    if not target:
        return False
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ("http", "https") and ref_url.netloc == test_url.netloc
