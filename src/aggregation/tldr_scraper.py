"""
TLDR AI News Scraper - Clean implementation focusing on id="ai" section
Includes full article content fetching
"""

import requests
from bs4 import BeautifulSoup
from typing import List, Optional, Dict, Any
from datetime import datetime
import re
import os
import time
from urllib.parse import urljoin

from .models import NewsItem, NewsCollection
from .database import DatabaseManager
from .content_fetcher import ContentFetcher
from .logging_config import get_logger, LoggedOperation, log_performance_metric

# Configure logging
logger = get_logger("tldr_scraper")

# Constants
MAX_ARTICLES_PER_SCRAPE = 20
MIN_TITLE_LENGTH = 10
MAX_SUMMARY_LENGTH = 500
REQUEST_TIMEOUT = 30


class TLDRAIScraper:
    """Simple web scraper for TLDR AI news using requests and BeautifulSoup"""
    
    def __init__(self, db_manager: DatabaseManager = None, fetch_content: bool = True):
        self.db_manager = db_manager or DatabaseManager()
        self.base_url = "https://tldr.tech/"
        self.fetch_content = fetch_content
        self.content_fetcher = ContentFetcher() if fetch_content else None
        
        # Request headers
        self.headers = {
            'User-Agent': 'TrendCreate/1.0 (Content Aggregation Tool)',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
    
    def scrape_ai_news(self) -> NewsCollection:
        """Main method to scrape AI news from TLDR with enhanced duplicate detection"""
        logger.info("Starting TLDR AI news scraping with duplicate detection")
        
        try:
            # Get the webpage content
            response = requests.get(self.base_url, headers=self.headers, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            
            # Parse HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find the AI section by id="ai"
            ai_section = soup.find('div', id='ai')
            
            if not ai_section:
                logger.warning("Could not find AI section with id='ai'")
                return NewsCollection(items=[], source="TLDR AI", collected_at=datetime.now())
            
            logger.info("Found AI section, extracting articles...")
            
            # Extract articles from AI section
            raw_articles = self._extract_articles_from_ai_section(ai_section)
            logger.info(f"Extracted {len(raw_articles)} raw articles")
            
            # Convert to NewsItem objects (database will handle duplicate detection)
            news_items = []
            for article_data in raw_articles:
                news_item = self._create_news_item(article_data)
                if news_item:
                    news_items.append(news_item)
            
            logger.info(f"Successfully created {len(news_items)} NewsItem objects")
            
            return NewsCollection(
                items=news_items,
                source="TLDR AI",
                collected_at=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Error during scraping: {e}")
            return NewsCollection(items=[], source="TLDR AI", collected_at=datetime.now())
    
    def _extract_articles_from_ai_section(self, ai_section) -> List[Dict[str, Any]]:
        """Extract article data from the AI section"""
        articles = []
        
        try:
            # Based on the HTML structure, articles are in divs with specific flex classes
            # Each article is in a div with classes like "w-full min-[480px]:w-auto min-[480px]:flex-shrink-0"
            article_containers = ai_section.find_all('div', class_=re.compile(r'w-full.*min-\[480px\]:w-auto'))
            
            logger.info(f"Found {len(article_containers)} potential articles")
            
            for container in article_containers:
                try:
                    article_data = self._extract_single_article(container)
                    if article_data:
                        articles.append(article_data)
                        
                        # Limit to max articles
                        if len(articles) >= MAX_ARTICLES_PER_SCRAPE:
                            break
                            
                except Exception as e:
                    logger.error(f"Error extracting single article: {e}")
                    continue
            
            logger.info(f"Successfully extracted {len(articles)} articles")
            return articles
            
        except Exception as e:
            logger.error(f"Error extracting articles from AI section: {e}")
            return []
    
    def _extract_single_article(self, container) -> Optional[Dict[str, Any]]:
        """Extract data from a single article container"""
        try:
            # Find the main article link (target="_blank" with utm_source=tldrai)
            main_link = container.find('a', {
                'target': '_blank',
                'href': re.compile(r'utm_source=tldrai')
            })
            
            if not main_link:
                return None
            
            # Extract link and make absolute
            href = main_link.get('href', '')
            if not href:
                return None
            
            link = urljoin(self.base_url, href) if not href.startswith('http') else href
            
            # Extract title from h3 element
            h3_element = container.find('h3')
            if not h3_element:
                return None
            
            title = h3_element.get_text(strip=True)
            if not title or len(title) < MIN_TITLE_LENGTH:
                return None
            
            # Extract date and category from span (e.g., "Jul 25 | AI")
            date_span = container.find('span', class_=re.compile(r'text-xs.*tracking-wider'))
            published_date = datetime.now()  # Default
            
            if date_span:
                date_text = date_span.get_text(strip=True)
                published_date = self._parse_date(date_text)
            
            # Extract image URL
            img_element = container.find('img')
            image_url = ""
            if img_element:
                image_url = img_element.get('src', '')
            
            # Extract read time from title (e.g., "(13 minute read)")
            read_time = ""
            read_time_match = re.search(r'\((\d+\s+minute\s+read)\)', title)
            if read_time_match:
                read_time = read_time_match.group(1)
                # Remove read time from title
                title = re.sub(r'\s*\(\d+\s+minute\s+read\)', '', title).strip()
            
            # Create summary (use title as summary for now)
            summary = title
            
            # Extract AI-related tags
            tags = self._extract_ai_tags(title)
            
            return {
                'title': title,
                'summary': summary,
                'link': link,
                'published_date': published_date,
                'image_url': image_url,
                'read_time': read_time,
                'tags': tags
            }
            
        except Exception as e:
            logger.error(f"Error extracting single article data: {e}")
            return None
    
    def _parse_date(self, date_text: str) -> datetime:
        """Parse date from TLDR format (e.g., 'Jul 25 | AI')"""
        try:
            # Extract just the date part (before |)
            date_part = date_text.split('|')[0].strip()
            
            # Parse dates like "Jul 25"
            current_year = datetime.now().year
            
            # Try to parse month and day
            match = re.search(r'(\w{3})\s+(\d{1,2})', date_part)
            if match:
                month_str, day_str = match.groups()
                try:
                    month_num = datetime.strptime(month_str, '%b').month
                    day_num = int(day_str)
                    return datetime(current_year, month_num, day_num)
                except:
                    pass
            
            # Fallback to current date
            logger.warning(f"Could not parse date '{date_text}', using current date")
            return datetime.now()
            
        except Exception as e:
            logger.error(f"Error parsing date '{date_text}': {e}")
            return datetime.now()
    
    def _extract_ai_tags(self, text: str) -> List[str]:
        """Extract AI-related tags from text"""
        ai_keywords = [
            'ai', 'artificial intelligence', 'machine learning', 'ml', 'deep learning',
            'neural network', 'chatgpt', 'gpt', 'llm', 'large language model',
            'openai', 'anthropic', 'google', 'microsoft', 'meta', 'nvidia',
            'automation', 'robotics', 'computer vision', 'nlp',
            'generative ai', 'stable diffusion', 'midjourney', 'dall-e',
            'transformer', 'bert', 'claude', 'gemini', 'cursor'
        ]
        
        found_tags = ['AI']  # Always include AI tag
        text_lower = text.lower()
        
        for keyword in ai_keywords:
            if keyword in text_lower and keyword.title() not in found_tags:
                found_tags.append(keyword.title())
        
        return found_tags
    
    def _create_news_item(self, article_data: Dict[str, Any]) -> Optional[NewsItem]:
        """Convert article data to NewsItem, optionally fetching full content"""
        try:
            # Start with empty content
            content = ""
            
            # Fetch full article content if enabled
            if self.fetch_content and self.content_fetcher:
                logger.info(f"Fetching content for: {article_data['title'][:50]}...")
                
                try:
                    content_result = self.content_fetcher.extract_content(article_data['link'])
                    
                    if content_result['success']:
                        content = content_result['cleaned_content']
                        logger.info(f"Successfully fetched {content_result['word_count']} words")
                        
                        # Add content metadata to tags if available
                        if content_result['content_type'] != 'unknown':
                            article_data['tags'] = article_data.get('tags', []) + [content_result['content_type']]
                    else:
                        logger.warning(f"Failed to fetch content: {content_result.get('error', 'Unknown error')}")
                        
                    # Small delay to be respectful to servers
                    time.sleep(1)
                    
                except Exception as e:
                    logger.error(f"Error fetching content for {article_data['link']}: {e}")
            
            return NewsItem(
                title=article_data['title'],
                summary=article_data['summary'],
                link=article_data['link'],
                source="TLDR AI",
                published_date=article_data['published_date'],
                content=content,
                tags=article_data.get('tags', ['AI']),
                image_url=article_data.get('image_url', ''),
                read_time=article_data.get('read_time', '')
            )
        except Exception as e:
            logger.error(f"Error creating NewsItem: {e}")
            return None
    
    def save_to_database(self, news_collection: NewsCollection) -> dict:
        """
        Save news items to database with detailed duplicate detection
        Returns detailed statistics about the save operation
        """
        try:
            logger.info(f"Attempting to save {len(news_collection.items)} articles to database")
            
            # Use enhanced save method that returns detailed stats
            stats = self.db_manager.save_news_items(news_collection.items)
            
            # Log detailed results
            logger.info(f"Save completed: {stats['saved']} saved, {stats['duplicates']} duplicates, {stats['errors']} errors")
            
            if stats['duplicate_reasons']:
                logger.info("Duplicate detection breakdown:")
                for reason, count in stats['duplicate_reasons'].items():
                    logger.info(f"  - {reason}: {count} items")
            
            return stats
            
        except Exception as e:
            logger.error(f"Error saving to database: {e}")
            return {
                'total': len(news_collection.items),
                'saved': 0,
                'duplicates': 0,
                'errors': len(news_collection.items),
                'duplicate_reasons': {},
                'processed_items': []
            }
    
    def get_duplicate_statistics(self, days: int = 30) -> dict:
        """Get duplicate detection statistics"""
        try:
            return self.db_manager.get_duplicate_stats(days)
        except Exception as e:
            logger.error(f"Error getting duplicate statistics: {e}")
            return {}
    
    def clean_old_duplicates(self, days: int = 90) -> int:
        """Clean old duplicate entries from database"""
        try:
            removed_count = self.db_manager.clean_old_duplicates(days)
            logger.info(f"Cleaned {removed_count} old duplicate entries")
            return removed_count
        except Exception as e:
            logger.error(f"Error cleaning old duplicates: {e}")
            return 0
    
    def export_to_markdown(self, news_collection: NewsCollection, filename: str = None) -> str:
        """Export news items to markdown format"""
        if not filename:
            today = datetime.now().strftime('%Y-%m-%d')
            content_dir = os.path.join(os.getcwd(), 'content', f'{today}-tldr-ai-news')
            os.makedirs(content_dir, exist_ok=True)
            filename = os.path.join(content_dir, 'ai_news.md')
        
        markdown_content = f"# TLDR AI News - {datetime.now().strftime('%Y-%m-%d')}\n\n"
        markdown_content += f"*Aggregated from TLDR AI newsletter*\n\n"
        markdown_content += f"**Total Articles:** {len(news_collection.items)}\n\n"
        
        for i, item in enumerate(news_collection.items, 1):
            markdown_content += f"## {i}. {item.title}\n\n"
            if item.read_time:
                markdown_content += f"**Read Time:** {item.read_time}\n"
            markdown_content += f"**Published:** {item.published_date.strftime('%Y-%m-%d')}\n"
            markdown_content += f"**Link:** [{item.domain}]({item.link})\n\n"
            
            if item.tags:
                markdown_content += f"**Tags:** {', '.join(item.tags)}\n\n"
            
            if item.image_url:
                markdown_content += f"![Article Image]({item.image_url})\n\n"
            
            markdown_content += "---\n\n"
        
        # Write to file
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        logger.info(f"Exported {len(news_collection.items)} articles to {filename}")
        return filename
    
    def get_recent_news(self, days: int = 1) -> NewsCollection:
        """Get recent news from database"""
        news_items = self.db_manager.get_recent_news(days=days, source="TLDR AI")
        return NewsCollection(
            items=news_items,
            source="TLDR AI",
            collected_at=datetime.now()
        )
    
    def close(self):
        """Close database connections and content fetcher"""
        if self.content_fetcher:
            self.content_fetcher.close()
        self.db_manager.close()
