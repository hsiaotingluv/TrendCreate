# Aggregation Module

Core news aggregation system for TrendCreate with intelligent content extraction and performance optimization.

## 🏗️ Module Architecture

```
src/aggregation/
├── models.py           # Unified NewsItem SQLAlchemy model
├── tldr_scraper.py     # Main scraper orchestrator  
├── content_fetcher.py  # Optimized content extraction
├── database.py         # Database operations
└── logging_config.py   # Comprehensive logging system
```

## 📄 Core Components

### `models.py` - Unified Data Model

**NewsItem Class**: Single SQLAlchemy model handling both business logic and persistence

```python
class NewsItem(Base):
    # Database fields
    id, title, url, summary, content, published_date, source, content_hash, created_at
    
    # Business methods
    @property
    def tags(self) -> List[str]           # Extract tags from content
    @property 
    def domain(self) -> str               # Parse domain from URL
    def generate_content_hash(self) -> str # SHA-256 for deduplication
```

**Key Features**:
- Unified model eliminates conversion overhead
- Built-in content hashing for duplicate detection
- Automatic tag extraction and domain parsing
- Database-ready with SQLAlchemy Base

### `content_fetcher.py` - Performance-Optimized Extraction

**ContentFetcher Class**: High-performance content extraction with intelligent optimization

```python
class ContentFetcher:
    def extract_content(self, url: str) -> Dict[str, Any]
    def _fetch_with_retries(self, url: str) -> Optional[requests.Response]
    def _clean_content(self, content: str) -> str
```

**Performance Features**:
- **Domain Blacklisting**: Skip slow/problematic domains
- **Fast Timeouts**: 8-second connection/read timeouts  
- **Retry Logic**: 2 attempts with 1-second delay
- **Universal Extraction**: Works with various article formats
- **Content Cleaning**: Remove ads, navigation, etc.

**Blacklist Configuration**:
```python
BLACKLISTED_DOMAINS = {
    'minihf.com',           # Known timeout issues
    # Add problematic domains here
}
```

### `tldr_scraper.py` - Main Orchestrator

**TLDRAIScraper Class**: Coordinates all aggregation operations

```python
class TLDRAIScraper:
    def __init__(self, fetch_content: bool = True)
    def scrape_ai_news(self) -> NewsCollection
    def save_to_database(self, news_collection: NewsCollection) -> Dict[str, int]
    def export_to_markdown(self, news_collection: NewsCollection) -> str
```

**Orchestration Features**:
- Scrapes TLDR AI newsletter pages
- Coordinates content fetching with performance optimization
- Manages database transactions with rollback support
- Generates professional markdown exports
- Comprehensive error handling and logging

### `logging_config.py` - Comprehensive Logging System

**Logging Features**: Multi-level logging with file rotation and performance tracking

```python
from logging_config import setup_logging, get_logger, LoggedOperation, log_performance_metric

# Setup logging
logger = setup_logging(log_level="INFO", log_to_file=True, log_to_console=True)

# Use context manager for operation logging
with LoggedOperation("fetch_articles", logger):
    # Operation code here
    pass

# Log performance metrics
log_performance_metric("content_extraction", duration, domain="example.com", status="success")
```

**Logging Structure**:
- **Daily Logs**: `logs/aggregation_YYYY-MM-DD.log` (rotated daily, 30-day retention)
- **Error Logs**: `logs/errors.log` (errors and critical only, 10MB rotation)
- **Performance Logs**: `logs/performance.log` (timing metrics, 5MB rotation)
- **Console Output**: INFO level and above for user feedback

### `database.py` - Database Operations

**DatabaseManager Class**: Handles all database interactions

```python
class DatabaseManager:
    def save_news_item(self, item: NewsItem) -> bool
    def get_recent_news(self, days: int, source: str) -> List[NewsItem]
    def is_duplicate(self, item: NewsItem) -> Tuple[bool, str]
```

**Database Features**:
- SQLite with SQLAlchemy ORM
- Transaction management with rollback
- Multiple duplicate detection strategies
- Efficient querying with date ranges
- Automatic schema creation

## 🚀 Performance Optimizations

### 1. Domain Blacklisting
Prevents timeouts from slow/problematic domains:
- **Before**: 30+ second timeouts per problematic URL
- **After**: Instant skip with fallback to TLDR summary
- **Impact**: 60+ seconds → 15-20 seconds total runtime

### 2. Intelligent Timeouts
Optimized for speed while maintaining reliability:
- Connection timeout: 8 seconds (vs 15s default)
- Read timeout: 8 seconds  
- Retry attempts: 2 (vs 3 default)
- Retry delay: 1 second (vs 2s default)

### 3. Unified Data Model
Single NewsItem class eliminates conversion overhead:
- **Before**: Separate dataclass + database model + conversions
- **After**: Single SQLAlchemy model with business methods
- **Impact**: Reduced complexity, faster operations

### 4. Content Optimization
Smart content processing for better quality:
- Remove navigation, ads, and boilerplate
- Extract main article content only
- Preserve formatting and structure
- Limit content length (50KB max)

## 🔄 Duplicate Detection

Multiple strategies ensure no duplicate content:

### 1. URL Matching
```python
existing_url = session.query(NewsItem).filter_by(url=item.url).first()
```

### 2. Content Hashing  
```python
content_hash = hashlib.sha256(content.encode()).hexdigest()
existing_hash = session.query(NewsItem).filter_by(content_hash=content_hash).first()
```

### 3. Title Similarity
Fuzzy matching for slight title variations

## 📊 Error Handling

Comprehensive error handling with graceful fallbacks:

### Network Errors
- **Timeouts**: Fallback to TLDR summary
- **Connection errors**: Skip with logging
- **HTTP errors**: Retry with exponential backoff

### Content Extraction Errors
- **Parse failures**: Use raw HTML as fallback
- **Empty content**: Use meta description or summary
- **Encoding issues**: Multiple encoding attempts

### Database Errors
- **Constraint violations**: Duplicate detection and skip
- **Transaction failures**: Rollback with error logging
- **Schema issues**: Automatic schema creation

## 🛠️ Configuration

### Environment Variables
```bash
# Optional: Configure database location
DATABASE_URL=sqlite:///custom_path/news.db

# Optional: Enable debug logging
LOG_LEVEL=DEBUG
```

### Performance Tuning
```python
# content_fetcher.py - Adjust timeouts
REQUEST_TIMEOUT = 8          # Connection/read timeout
MAX_RETRIES = 2              # Retry attempts
RETRY_DELAY = 1              # Delay between retries
MAX_CONTENT_LENGTH = 50000   # Max content size

# Add domains to blacklist
BLACKLISTED_DOMAINS.add('slow-domain.com')
```

## 📈 Monitoring & Metrics

Built-in performance monitoring:

### Timing Metrics
- Total aggregation time
- Per-article content fetching time
- Database operation timing
- Export generation time

### Success Metrics
- Articles found vs. articles with content
- Duplicate detection statistics
- Error rates by domain
- Content extraction success rates

### Logging
```python
from aggregation.logging_config import setup_logging, get_logger, LoggedOperation

# Initialize logging
logger = setup_logging(log_level="INFO")

# Get module-specific logger
logger = get_logger("content_fetcher")

# Use operation context manager
with LoggedOperation("scraping_operation", logger):
    # Your code here
    pass

# Logs are automatically written to:
# - logs/aggregation_2025-07-27.log (daily rotation)
# - logs/errors.log (errors only)
# - logs/performance.log (timing metrics)
```

**Log Output Example**:
```
2025-07-27 14:30:15 | aggregation.content_fetcher | INFO     | extract_content:67 | Fetching content from: example.com
2025-07-27 14:30:16 | aggregation.content_fetcher | INFO     | extract_content:89 | Successfully extracted 1,234 words from example.com in 1.23s
2025-07-27 14:30:16 | aggregation.performance     | INFO     | content_extraction | 1.234s | domain=example.com | status=success | word_count=1234
```

## 🧪 Testing

### Manual Testing
```python
# Test content fetcher
from aggregation.content_fetcher import ContentFetcher
fetcher = ContentFetcher()
result = fetcher.extract_content('https://example.com/article')

# Test scraper
from aggregation.tldr_scraper import TLDRAIScraper
scraper = TLDRAIScraper(fetch_content=True)
news = scraper.scrape_ai_news()
```

### Performance Testing
```python
import time
start_time = time.time()
# Run aggregation
duration = time.time() - start_time
print(f"Aggregation completed in {duration:.2f} seconds")
```

## 🔧 Extension Points

### Adding New Content Sources
1. Extend `TLDRAIScraper` with new scraping methods
2. Update `NewsItem.source` field for new sources
3. Add source-specific parsing logic

### Custom Content Extraction
1. Extend `ContentFetcher` with domain-specific extractors
2. Add custom cleaning rules in `_clean_content`
3. Implement source-specific parsing strategies

### Database Extensions
1. Extend `NewsItem` model with additional fields
2. Add new indexes for query optimization
3. Implement custom duplicate detection logic

## 📋 Dependencies

**Core Dependencies**:
- `requests>=2.31.0` - HTTP requests
- `beautifulsoup4>=4.12.0` - HTML parsing
- `sqlalchemy>=2.0.0` - Database ORM
- `python-dateutil>=2.8.0` - Date parsing

**Performance Dependencies**:
- `lxml>=4.9.0` - Fast XML/HTML parsing
- `tqdm>=4.65.0` - Progress bars

See `../requirements.txt` for complete dependency list.

## 🚀 Usage

This module is designed to be used through the main execution script:

```bash
# Run daily aggregation
python scripts/daily_aggregation.py
```

The module provides a clean, unified API through the `TLDRAIScraper` class with comprehensive logging, performance optimization, and error handling built-in.
