"""
Content fetcher for extracting full article content from URLs
"""

import requests
from bs4 import BeautifulSoup
from typing import Optional, Dict, Any
import time
import re
from urllib.parse import urljoin, urlparse

from .logging_config import get_logger, log_performance_metric

logger = get_logger("content_fetcher")

# Content extraction constants
REQUEST_TIMEOUT = 8      # Reduced from 15 to 8 seconds
MAX_RETRIES = 2          # Reduced from 3 to 2 retries
RETRY_DELAY = 1          # Reduced from 2 to 1 second delay
MAX_CONTENT_LENGTH = 50000  # Maximum content length to store

# Blacklisted domains that are known to be slow/problematic
BLACKLISTED_DOMAINS = {
    'minihf.com',           # Known to timeout frequently
    'slow-site.com',        # Add other problematic domains here
    # Add more as needed
}


class ContentFetcher:
    """Fetches and extracts full article content from URLs"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'TrendCreate/1.0 Content Aggregator (Educational Research)',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
    
    def extract_content(self, url: str) -> Dict[str, Any]:
        """
        Extract full content from a given URL
        Returns dict with content, metadata, and extraction info
        """
        start_time = time.time()
        result = {
            'content': '',
            'cleaned_content': '',
            'title': '',
            'meta_description': '',
            'word_count': 0,
            'success': False,
            'error': None,
            'domain': '',
            'content_type': 'unknown'
        }
        
        try:
            # Extract domain for logging
            domain = urlparse(url).netloc
            result['domain'] = domain
            
            logger.debug(f"Starting content extraction for: {url}")
            
            # Check if domain is blacklisted
            if domain in BLACKLISTED_DOMAINS:
                result['error'] = f'Domain {domain} is blacklisted (known to be slow/problematic)'
                logger.warning(f"Skipping blacklisted domain: {domain}")
                log_performance_metric("content_extraction", time.time() - start_time, 
                                     domain=domain, status="blacklisted", url=url)
                return result
            
            logger.info(f"Fetching content from: {domain}")
            
            # Fetch the page content
            response = self._fetch_with_retries(url)
            if not response:
                result['error'] = 'Failed to fetch page'
                logger.error(f"Failed to fetch page: {url}")
                log_performance_metric("content_extraction", time.time() - start_time, 
                                     domain=domain, status="fetch_failed", url=url)
                return result
            
            logger.debug(f"Successfully fetched page: {len(response.content)} bytes")
            
            # Parse HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract title
            title_tag = soup.find('title')
            if title_tag:
                result['title'] = title_tag.get_text().strip()
                logger.debug(f"Extracted title: {result['title'][:100]}...")
            
            # Extract meta description
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            if meta_desc:
                result['meta_description'] = meta_desc.get('content', '').strip()
                logger.debug(f"Extracted meta description: {len(result['meta_description'])} chars")
            
            # Extract main content based on domain/site type
            content = self._extract_main_content(soup, domain)
            
            if content:
                result['content'] = content
                result['cleaned_content'] = self._clean_content(content)
                result['word_count'] = len(result['cleaned_content'].split())
                result['success'] = True
                result['content_type'] = self._detect_content_type(domain, soup)
                
                duration = time.time() - start_time
                logger.info(f"Successfully extracted {result['word_count']} words from {domain} in {duration:.2f}s")
                log_performance_metric("content_extraction", duration, 
                                     domain=domain, status="success", word_count=result['word_count'], url=url)
            else:
                result['error'] = 'No content found'
                duration = time.time() - start_time
                logger.warning(f"No content extracted from {domain} after {duration:.2f}s")
                log_performance_metric("content_extraction", duration, 
                                     domain=domain, status="no_content", url=url)
            
        except Exception as e:
            result['error'] = str(e)
            duration = time.time() - start_time
            logger.error(f"Error extracting content from {url} after {duration:.2f}s: {e}")
            log_performance_metric("content_extraction", duration, 
                                 domain=domain, status="error", error=str(e), url=url)
        
        return result
    
    def _fetch_with_retries(self, url: str) -> Optional[requests.Response]:
        """Fetch URL with retries and proper error handling"""
        domain = urlparse(url).netloc
        
        for attempt in range(MAX_RETRIES):
            try:
                logger.info(f"Fetching {domain} (attempt {attempt + 1}/{MAX_RETRIES})")
                response = self.session.get(url, timeout=REQUEST_TIMEOUT)
                response.raise_for_status()
                return response
                
            except requests.exceptions.Timeout:
                logger.warning(f"Timeout for {domain} (attempt {attempt + 1})")
            except requests.exceptions.ConnectionError:
                logger.warning(f"Connection error for {domain} (attempt {attempt + 1})")
            except requests.exceptions.RequestException as e:
                logger.warning(f"Request failed for {domain}: {e}")
                
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY)
        
        logger.error(f"All {MAX_RETRIES} attempts failed for {domain}")
        return None
    
    def _extract_main_content(self, soup: BeautifulSoup, domain: str) -> str:
        """Extract main content using a simplified, universal approach"""
        
        # Remove unwanted elements first
        for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside', 'ad', 'iframe']):
            element.decompose()
        
        # Try content selectors in order of preference (most specific to general)
        selectors = [
            'article',           # Most semantic and widely used
            'main',              # HTML5 semantic main content
            '.content',          # Common class name
            '.post-content',     # Blog posts
            '.entry-content',    # WordPress and similar CMS
            '#content',          # Common ID
            'body'               # Fallback
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                text = element.get_text().strip()
                # Only return if we have substantial content (more than 100 words)
                if len(text.split()) > 100:
                    return text
        
        # Last resort: get all text from body
        body = soup.find('body')
        return body.get_text().strip() if body else ""
    
    def _clean_content(self, content: str) -> str:
        """Clean and normalize extracted content"""
        if not content:
            return ""
        
        # Remove extra whitespace
        content = re.sub(r'\s+', ' ', content)
        
        # Remove excessive newlines
        content = re.sub(r'\n\s*\n\s*\n+', '\n\n', content)
        
        # Trim content if too long
        if len(content) > MAX_CONTENT_LENGTH:
            content = content[:MAX_CONTENT_LENGTH] + "... [Content truncated]"
        
        return content.strip()
    
    def _detect_content_type(self, domain: str, soup: BeautifulSoup) -> str:
        """Detect the type of content based on domain"""
        if 'arxiv.org' in domain:
            return 'academic_paper'
        elif 'github.com' in domain:
            return 'code_repository'
        elif any(blog_domain in domain for blog_domain in ['medium.com', 'substack.com', 'blog.']):
            return 'blog_post'
        elif any(news_domain in domain for news_domain in ['venturebeat.com', 'tomshardware.com', 'techcrunch.com']):
            return 'news_article'
        else:
            return 'general_article'
    
    def close(self):
        """Close the session"""
        self.session.close()


def fetch_article_content(url: str) -> Dict[str, Any]:
    """Convenience function to fetch content from a single URL"""
    fetcher = ContentFetcher()
    try:
        return fetcher.extract_content(url)
    finally:
        fetcher.close()
