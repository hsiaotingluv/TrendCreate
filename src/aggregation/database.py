"""
Database management for the TrendCreate content aggregation system.
"""

from datetime import datetime
from typing import List, Optional, Set
import os
import hashlib
import re
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .models import NewsItem, Base
from .logging_config import get_logger, log_performance_metric

# Configure logging
logger = get_logger("database")


class DatabaseManager:
    """Manages database operations for news items with enhanced duplicate detection"""
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            # Default to data directory
            data_dir = os.path.join(os.getcwd(), 'data')
            os.makedirs(data_dir, exist_ok=True)
            db_path = os.path.join(data_dir, 'trendcreate.db')
        
        self.db_path = db_path
        self.engine = create_engine(f'sqlite:///{db_path}', echo=False)
        self.SessionLocal = sessionmaker(bind=self.engine)
        
        # Create tables
        self.create_tables()
        
        # Cache for recent links to avoid repeated database queries
        self._link_cache: Set[str] = set()
        self._title_hash_cache: Set[str] = set()
        self._load_caches()
    
    def _normalize_title(self, title: str) -> str:
        """Normalize title for duplicate detection"""
        import re
        # Remove read time, extra spaces, and normalize case
        normalized = re.sub(r'\s*\(\d+\s+minute\s+read\)\s*', '', title, flags=re.IGNORECASE)
        normalized = re.sub(r'\s+', ' ', normalized.strip().lower())
        return normalized
    
    def _generate_title_hash(self, title: str) -> str:
        """Generate MD5 hash of normalized title"""
        normalized_title = self._normalize_title(title)
        return hashlib.md5(normalized_title.encode('utf-8')).hexdigest()
    
    def _generate_content_hash(self, content: str) -> str:
        """Generate MD5 hash of content"""
        if not content:
            return ""
        # Normalize content by removing extra spaces and lowercasing
        normalized_content = re.sub(r'\s+', ' ', content.strip().lower())
        return hashlib.md5(normalized_content.encode('utf-8')).hexdigest()
    
    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL"""
        try:
            from urllib.parse import urlparse
            return urlparse(url).netloc.lower()
        except:
            return ""
    
    def _load_caches(self):
        """Load recent links and title hashes into cache for faster duplicate detection"""
        session = self.get_session()
        try:
            # Load recent links (last 30 days)
            from datetime import timedelta
            cutoff_date = datetime.now() - timedelta(days=30)
            
            recent_items = session.query(NewsItem.link, NewsItem.title_hash).filter(
                NewsItem.created_at >= cutoff_date
            ).all()
            
            self._link_cache = {item.link for item in recent_items}
            self._title_hash_cache = {item.title_hash for item in recent_items if item.title_hash}
            
            logger.info(f"Loaded {len(self._link_cache)} links and {len(self._title_hash_cache)} title hashes into cache")
            
        except Exception as e:
            logger.error(f"Error loading caches: {e}")
        finally:
            session.close()
    
    def create_tables(self):
        """Create database tables if they don't exist"""
        try:
            Base.metadata.create_all(bind=self.engine)
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Error creating database tables: {e}")
            raise
    
    def get_session(self):
        """Get a database session"""
        return self.SessionLocal()
    
    def is_duplicate(self, news_item: NewsItem) -> tuple[bool, str]:
        """
        Check if news item is a duplicate using multiple methods
        Returns (is_duplicate, reason)
        """
        # Method 1: Quick cache check for exact link match
        if news_item.link in self._link_cache:
            return True, "exact_link_match"
        
        # Method 2: Quick cache check for title hash
        title_hash = self._generate_title_hash(news_item.title)
        if title_hash in self._title_hash_cache:
            return True, "similar_title_match"
        
        # Method 3: Database check for similar content within same domain
        session = self.get_session()
        try:
            domain = self._extract_domain(news_item.link)
            
            # Check for similar titles in same domain within last 7 days
            from datetime import timedelta
            cutoff_date = datetime.now() - timedelta(days=7)
            
            similar_items = session.query(NewsItem).filter(
                NewsItem.domain_field == domain,
                NewsItem.title_hash == title_hash,
                NewsItem.published_date >= cutoff_date
            ).first()
            
            if similar_items:
                return True, "similar_content_same_domain"
            
            # Check for exact link in database (fallback)
            existing = session.query(NewsItem).filter_by(link=news_item.link).first()
            if existing:
                return True, "exact_link_database"
            
            return False, "not_duplicate"
            
        except Exception as e:
            logger.error(f"Error checking for duplicates: {e}")
            return False, "error_checking"
        finally:
            session.close()
    
    def save_news_item(self, news_item: NewsItem) -> tuple[bool, str]:
        """
        Save a single news item to database with enhanced duplicate detection
        Returns (success, message)
        """
        # Check for duplicates first
        is_dup, reason = self.is_duplicate(news_item)
        if is_dup:
            logger.info(f"Skipping duplicate article: {news_item.title[:50]}... (Reason: {reason})")
            return False, f"duplicate_{reason}"
        
        session = self.get_session()
        try:
            # Generate hashes and extract domain
            title_hash = self._generate_title_hash(news_item.title)
            content_hash = self._generate_content_hash(news_item.content)
            domain = self._extract_domain(news_item.link)
            
            # Set the additional fields on the news_item
            news_item.title_hash = title_hash
            news_item.content_hash = content_hash
            news_item.domain_field = domain
            
            session.add(news_item)
            session.commit()
            
            # Update caches
            self._link_cache.add(news_item.link)
            self._title_hash_cache.add(title_hash)
            
            logger.info(f"Saved news item: {news_item.title[:50]}...")
            return True, "saved_successfully"
            
        except Exception as e:
            logger.error(f"Error saving news item: {e}")
            session.rollback()
            return False, f"error_{str(e)}"
        finally:
            session.close()
    
    def save_news_items(self, news_items: List[NewsItem]) -> dict:
        """
        Save multiple news items to database with detailed reporting
        Returns dict with statistics
        """
        stats = {
            'total': len(news_items),
            'saved': 0,
            'duplicates': 0,
            'errors': 0,
            'duplicate_reasons': {},
            'processed_items': []
        }
        
        for item in news_items:
            success, message = self.save_news_item(item)
            
            item_info = {
                'title': item.title[:50] + "..." if len(item.title) > 50 else item.title,
                'link': item.link,
                'status': message
            }
            
            if success:
                stats['saved'] += 1
                item_info['result'] = 'saved'
            elif message.startswith('duplicate_'):
                stats['duplicates'] += 1
                reason = message.replace('duplicate_', '')
                stats['duplicate_reasons'][reason] = stats['duplicate_reasons'].get(reason, 0) + 1
                item_info['result'] = 'duplicate'
            else:
                stats['errors'] += 1
                item_info['result'] = 'error'
            
            stats['processed_items'].append(item_info)
        
        logger.info(f"Batch save completed: {stats['saved']} saved, {stats['duplicates']} duplicates, {stats['errors']} errors")
        return stats
    
    def get_duplicate_stats(self, days: int = 30) -> dict:
        """Get statistics about duplicates in the database"""
        session = self.get_session()
        try:
            from datetime import timedelta
            cutoff_date = datetime.now() - timedelta(days=days)
            
            # Count items by domain
            domain_counts = session.query(
                NewsItem.domain_field, 
                session.query(NewsItem).filter(
                    NewsItem.domain_field == NewsItem.domain_field,
                    NewsItem.created_at >= cutoff_date
                ).count().label('count')
            ).filter(NewsItem.created_at >= cutoff_date).group_by(NewsItem.domain_field).all()
            
            # Find potential duplicates by title hash
            title_duplicates = session.query(
                NewsItem.title_hash,
                session.query(NewsItem).filter(
                    NewsItem.title_hash == NewsItem.title_hash
                ).count().label('count')
            ).group_by(NewsItem.title_hash).having(
                session.query(NewsItem).filter(
                    NewsItem.title_hash == NewsItem.title_hash
                ).count() > 1
            ).all()
            
            return {
                'domain_distribution': dict(domain_counts),
                'potential_title_duplicates': len(title_duplicates),
                'total_items_checked': session.query(NewsItem).filter(
                    NewsItem.created_at >= cutoff_date
                ).count()
            }
            
        except Exception as e:
            logger.error(f"Error getting duplicate stats: {e}")
            return {}
        finally:
            session.close()
    
    def clean_old_duplicates(self, days: int = 90) -> int:
        """Remove old potential duplicate entries, keeping the newest one"""
        session = self.get_session()
        try:
            from datetime import timedelta
            cutoff_date = datetime.now() - timedelta(days=days)
            
            # Find groups of items with same title_hash
            duplicates = session.query(NewsItem.title_hash).filter(
                NewsItem.created_at <= cutoff_date
            ).group_by(NewsItem.title_hash).having(
                session.query(NewsItem).filter(
                    NewsItem.title_hash == NewsItem.title_hash
                ).count() > 1
            ).all()
            
            removed_count = 0
            for (title_hash,) in duplicates:
                # Get all items with this title hash, ordered by date
                items = session.query(NewsItem).filter(
                    NewsItem.title_hash == title_hash,
                    NewsItem.created_at <= cutoff_date
                ).order_by(NewsItem.created_at.desc()).all()
                
                # Keep the newest one, remove the rest
                for item in items[1:]:
                    session.delete(item)
                    removed_count += 1
            
            session.commit()
            logger.info(f"Cleaned {removed_count} old duplicate entries")
            return removed_count
            
        except Exception as e:
            logger.error(f"Error cleaning old duplicates: {e}")
            session.rollback()
            return 0
        finally:
            session.close()
    
    def get_recent_news(self, days: int = 7, limit: int = 50, source: str = None) -> List[NewsItem]:
        """Get recent news items from database"""
        session = self.get_session()
        try:
            query = session.query(NewsItem)
            
            # Filter by source if specified
            if source:
                query = query.filter(NewsItem.source == source)
            
            # Get recent items
            from datetime import timedelta
            cutoff_date = datetime.now() - timedelta(days=days)
            query = query.filter(NewsItem.published_date >= cutoff_date)
            
            # Order and limit
            news_items = query.order_by(NewsItem.published_date.desc()).limit(limit).all()
            
            return news_items
            
        except Exception as e:
            logger.error(f"Error retrieving news items: {e}")
            return []
        finally:
            session.close()
    
    def get_all_sources(self) -> List[str]:
        """Get list of all sources in database"""
        session = self.get_session()
        try:
            sources = session.query(NewsItem.source).distinct().all()
            return [source[0] for source in sources]
        except Exception as e:
            logger.error(f"Error getting sources: {e}")
            return []
        finally:
            session.close()
    
    def close(self):
        """Close database connections"""
        self.engine.dispose()
        logger.info("Database connections closed")
