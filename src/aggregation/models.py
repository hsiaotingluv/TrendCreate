"""
Data models for the TrendCreate content aggregation system.
"""

from datetime import datetime
from typing import List, Optional
from urllib.parse import urlparse
from dataclasses import dataclass
from sqlalchemy import Column, Integer, String, DateTime, Text, Index
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class NewsItem(Base):
    """Unified model for news articles - handles both application logic and database persistence"""
    __tablename__ = 'news_items'
    
    # Database columns
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(500), nullable=False)
    summary = Column(Text)
    link = Column(String(1000), nullable=False, unique=True)
    source = Column(String(100), nullable=False)
    published_date = Column(DateTime, nullable=False)
    content = Column(Text)
    tags_str = Column('tags', String(500))  # Store as comma-separated string
    image_url = Column(String(1000))
    read_time = Column(String(50))
    
    # Enhanced duplicate detection fields
    title_hash = Column(String(64), nullable=False)
    content_hash = Column(String(64))
    domain_field = Column('domain', String(200))  # Store domain as database field
    
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Indexes for faster duplicate detection
    __table_args__ = (
        Index('idx_title_hash', 'title_hash'),
        Index('idx_content_hash', 'content_hash'),
        Index('idx_domain_date', 'domain', 'published_date'),
        Index('idx_source_date', 'source', 'published_date'),
    )
    
    def __init__(self, title: str, summary: str, link: str, source: str, 
                 published_date: datetime, content: str = "", tags: List[str] = None, 
                 image_url: str = "", read_time: str = "", **kwargs):
        """Initialize NewsItem with both constructor args and SQLAlchemy kwargs"""
        self.title = title
        self.summary = summary
        self.link = link
        self.source = source
        self.published_date = published_date
        self.content = content
        self.tags = tags or []
        self.image_url = image_url
        self.read_time = read_time
        
        # Handle SQLAlchemy fields if provided
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    @property
    def tags(self) -> List[str]:
        """Get tags as list"""
        if hasattr(self, '_tags'):
            return self._tags
        return self.tags_str.split(',') if self.tags_str else []
    
    @tags.setter
    def tags(self, value: List[str]):
        """Set tags from list"""
        self._tags = value or []
        self.tags_str = ','.join(self._tags) if self._tags else ''
    
    
    @property
    def domain(self) -> str:
        """Extract domain from link"""
        try:
            return urlparse(self.link).netloc
        except:
            return ""
    
    @domain.setter
    def domain(self, value: str):
        """Set domain field for database storage"""
        self.domain_field = value
    
    def to_dict(self) -> dict:
        """Convert to dictionary for database storage"""
        return {
            'title': self.title,
            'summary': self.summary,
            'link': self.link,
            'source': self.source,
            'published_date': self.published_date,
            'content': self.content,
            'tags': ','.join(self.tags) if self.tags else '',
            'image_url': self.image_url,
            'read_time': self.read_time
        }


@dataclass
class NewsCollection:
    """Represents a collection of news items"""
    items: List[NewsItem]
    source: str
    collected_at: datetime
    
    def __len__(self) -> int:
        return len(self.items)
    
    def add_item(self, item: NewsItem):
        """Add a news item to the collection"""
        self.items.append(item)
    
    def filter_by_tags(self, tags: List[str]) -> 'NewsCollection':
        """Filter items by tags"""
        filtered_items = []
        for item in self.items:
            if any(tag.lower() in [t.lower() for t in item.tags] for tag in tags):
                filtered_items.append(item)
        
        return NewsCollection(
            items=filtered_items,
            source=self.source,
            collected_at=self.collected_at
        )
    
    def sort_by_date(self, ascending: bool = False) -> 'NewsCollection':
        """Sort items by publication date"""
        sorted_items = sorted(
            self.items,
            key=lambda x: x.published_date,
            reverse=not ascending
        )
        
        return NewsCollection(
            items=sorted_items,
            source=self.source,
            collected_at=self.collected_at
        )
