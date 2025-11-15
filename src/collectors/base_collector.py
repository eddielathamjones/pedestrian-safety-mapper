"""
Base class for all data collectors

Provides common functionality for API clients:
- Rate limiting
- Error handling
- Retry logic
- Progress tracking
- Caching
"""

import time
import hashlib
import json
from pathlib import Path
from typing import Optional, Dict, Any, Callable
from functools import wraps
from datetime import datetime, timedelta

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from loguru import logger
from diskcache import Cache


class RateLimiter:
    """Simple rate limiter using token bucket algorithm"""

    def __init__(self, calls_per_second: float = 1.0):
        self.calls_per_second = calls_per_second
        self.min_interval = 1.0 / calls_per_second
        self.last_call = 0.0

    def wait(self):
        """Wait if necessary to respect rate limit"""
        elapsed = time.time() - self.last_call
        if elapsed < self.min_interval:
            time.sleep(self.min_interval - elapsed)
        self.last_call = time.time()


class BaseCollector:
    """
    Base class for all data collectors

    Provides:
    - HTTP session with retry logic
    - Rate limiting
    - Response caching
    - Error handling
    - Progress tracking
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        rate_limit: float = 1.0,
        cache_dir: Optional[Path] = None,
        cache_ttl: int = 3600,
        timeout: int = 30
    ):
        """
        Initialize base collector

        Args:
            api_key: API key for authentication
            rate_limit: Maximum requests per second
            cache_dir: Directory for response cache
            cache_ttl: Cache time-to-live in seconds (default: 1 hour)
            timeout: Request timeout in seconds
        """
        self.api_key = api_key
        self.timeout = timeout

        # Rate limiter
        self.rate_limiter = RateLimiter(calls_per_second=rate_limit)

        # HTTP session with retry logic
        self.session = self._create_session()

        # Response cache
        if cache_dir:
            self.cache = Cache(str(cache_dir))
            self.cache_ttl = cache_ttl
        else:
            self.cache = None

        # Statistics
        self.stats = {
            'requests_made': 0,
            'cache_hits': 0,
            'errors': 0,
            'start_time': datetime.now()
        }

    def _create_session(self) -> requests.Session:
        """Create requests session with retry logic"""
        session = requests.Session()

        # Retry strategy
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST"]
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        return session

    def _cache_key(self, url: str, params: Optional[Dict] = None) -> str:
        """Generate cache key from URL and parameters"""
        key_data = f"{url}:{json.dumps(params, sort_keys=True)}"
        return hashlib.md5(key_data.encode()).hexdigest()

    def _get_cached(self, cache_key: str) -> Optional[Any]:
        """Get cached response if available and not expired"""
        if not self.cache:
            return None

        try:
            value, timestamp = self.cache.get(cache_key, (None, None))
            if value and timestamp:
                age = (datetime.now() - timestamp).total_seconds()
                if age < self.cache_ttl:
                    self.stats['cache_hits'] += 1
                    logger.debug(f"Cache hit: {cache_key[:8]}... (age: {age:.0f}s)")
                    return value
                else:
                    # Expired
                    self.cache.delete(cache_key)
        except Exception as e:
            logger.warning(f"Cache read error: {e}")

        return None

    def _set_cached(self, cache_key: str, value: Any):
        """Store response in cache"""
        if not self.cache:
            return

        try:
            self.cache.set(cache_key, (value, datetime.now()))
        except Exception as e:
            logger.warning(f"Cache write error: {e}")

    def request(
        self,
        method: str,
        url: str,
        params: Optional[Dict] = None,
        headers: Optional[Dict] = None,
        use_cache: bool = True,
        **kwargs
    ) -> requests.Response:
        """
        Make HTTP request with rate limiting, caching, and error handling

        Args:
            method: HTTP method (GET, POST, etc.)
            url: Request URL
            params: Query parameters
            headers: Request headers
            use_cache: Whether to use cache for GET requests
            **kwargs: Additional arguments for requests

        Returns:
            Response object

        Raises:
            requests.RequestException: On request failure
        """
        # Check cache for GET requests
        if use_cache and method.upper() == 'GET':
            cache_key = self._cache_key(url, params)
            cached = self._get_cached(cache_key)
            if cached:
                # Create mock response object
                response = requests.Response()
                response.status_code = 200
                response._content = json.dumps(cached).encode()
                response.headers['X-Cache'] = 'HIT'
                return response

        # Rate limiting
        self.rate_limiter.wait()

        # Make request
        try:
            response = self.session.request(
                method=method,
                url=url,
                params=params,
                headers=headers,
                timeout=self.timeout,
                **kwargs
            )

            response.raise_for_status()
            self.stats['requests_made'] += 1

            # Cache successful GET requests
            if use_cache and method.upper() == 'GET' and response.status_code == 200:
                try:
                    cache_key = self._cache_key(url, params)
                    self._set_cached(cache_key, response.json())
                except Exception:
                    pass  # Not all responses are JSON

            return response

        except requests.RequestException as e:
            self.stats['errors'] += 1
            logger.error(f"Request failed: {method} {url} - {e}")
            raise

    def get(self, url: str, **kwargs) -> requests.Response:
        """Convenience method for GET requests"""
        return self.request('GET', url, **kwargs)

    def post(self, url: str, **kwargs) -> requests.Response:
        """Convenience method for POST requests"""
        return self.request('POST', url, **kwargs)

    def test_connection(self) -> bool:
        """
        Test API connection - should be implemented by subclasses

        Returns:
            True if connection successful, False otherwise
        """
        raise NotImplementedError("Subclasses must implement test_connection()")

    def get_stats(self) -> Dict[str, Any]:
        """Get collector statistics"""
        runtime = (datetime.now() - self.stats['start_time']).total_seconds()

        return {
            **self.stats,
            'runtime_seconds': runtime,
            'requests_per_second': self.stats['requests_made'] / runtime if runtime > 0 else 0,
            'cache_hit_rate': self.stats['cache_hits'] / max(1, self.stats['requests_made'] + self.stats['cache_hits']),
            'error_rate': self.stats['errors'] / max(1, self.stats['requests_made'])
        }

    def close(self):
        """Clean up resources"""
        if self.session:
            self.session.close()

        if self.cache:
            self.cache.close()


def retry_on_failure(max_retries: int = 3, delay: float = 1.0, backoff: float = 2.0):
    """
    Decorator for retrying functions on failure

    Args:
        max_retries: Maximum number of retry attempts
        delay: Initial delay between retries (seconds)
        backoff: Multiplier for delay after each retry
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            current_delay = delay
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries:
                        logger.warning(
                            f"{func.__name__} failed (attempt {attempt + 1}/{max_retries + 1}): {e}. "
                            f"Retrying in {current_delay:.1f}s..."
                        )
                        time.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        logger.error(f"{func.__name__} failed after {max_retries + 1} attempts")

            raise last_exception

        return wrapper
    return decorator


# Example usage
if __name__ == '__main__':
    # Example of using BaseCollector
    class ExampleCollector(BaseCollector):
        def test_connection(self):
            try:
                response = self.get('https://httpbin.org/get')
                return response.status_code == 200
            except Exception as e:
                logger.error(f"Connection test failed: {e}")
                return False

    collector = ExampleCollector(rate_limit=2.0)

    if collector.test_connection():
        print("✓ Connection successful!")

        # Make some test requests
        for i in range(3):
            response = collector.get('https://httpbin.org/uuid')
            print(f"Request {i + 1}: {response.json()}")

        # Show stats
        print("\nStatistics:")
        stats = collector.get_stats()
        for key, value in stats.items():
            print(f"  {key}: {value}")

    collector.close()
