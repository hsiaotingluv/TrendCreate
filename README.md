# TrendCre- **📝 Comprehensive Logging**: Multi-level logging with file ro## 📈 Sample Output

```
## �️ Development

```bash
# ## 📋 Troubleshooting

**Slow Performance**: Check network connectivity, consider adding domains to blacklist
**Missing Content**: Verify URLs are accessible, check if domains are blacklisted
**Database Issues**: Ensure SQLite permissions and disk spacerements
Python 3.8+
Dependencies: requests, beautifulsoup4, sqlalchemy, tqdm

# Key Files
src/aggregation/        # Core module (see module README)
scripts/daily_aggregation.py  # Main execution script
requirements.txt        # All dependencies
```ent fetching enabled (with domain blacklisting for speed)
🔍 Step 1/5: Checking existing database content... ✅
📰 Step 2/5: Scraping latest AI news... ✅ Found 8 articles
📄 Step 3/5: Fetching full article content... ✅ 6/8 with content
💾 Step 4/5: Saving to database... ✅ Saved: 3, Duplicates: 5
📝 Step 5/5: Exporting to markdown... ✅ Exported to: exports/tldr_ai_news_2025-07-27.md
```

## 🗄️ Database & Exporterformance tracking
- **💾 Robust Storage**: SQLite database with comprehensive metadatae - TLDR AI News Aggregator

A high-performance news aggregation system that scrapes, processes, and stores AI-related articles from TLDR AI newsletter with intelligent content extraction and optimization features.

## 🚀 Key Features

- **🔄 Full Content Extraction**: Fetches complete article content from original sources
- **⚡ Smart Performance**: Domain blacklisting prevents timeouts, 15-20s total runtime
- **🎯 Intelligent Deduplication**: Multiple strategies prevent duplicate content
- **📊 Progress Visualization**: Real-time progress bars for all operations
- **� Comprehensive Logging**: Multi-level logging with file rotation and performance tracking
- **�💾 Robust Storage**: SQLite database with comprehensive metadata
- **📄 Markdown Export**: Professional formatted reports
- **🛡️ Error Resilience**: Graceful fallbacks and comprehensive error handling

## ⚡ Quick Start

```bash
# Clone and setup
git clone https://github.com/hsiaotingluv/TrendCreate.git
cd TrendCreate
pip install -r requirements.txt

# Run daily aggregation
python scripts/daily_aggregation.py
```

## 📊 Performance

- **⏱️ Total Runtime**: 15-20 seconds (optimized from 60+ seconds)
- **🚀 Content Fetching**: ~5-10 seconds for 8 articles
- **💾 Database Operations**: <1 second
- **📈 Success Rate**: High reliability with fallback strategies

## 📁 Architecture

```
TrendCreate/
├── src/aggregation/           # Core aggregation module
│   ├── models.py             # Unified NewsItem SQLAlchemy model
│   ├── tldr_scraper.py       # Main scraper orchestrator
│   ├── content_fetcher.py    # Optimized content extraction
│   ├── database.py           # Database operations
│   └── logging_config.py     # Comprehensive logging system
├── scripts/
│   └── daily_aggregation.py  # Main execution script
├── data/                     # SQLite database storage
├── logs/                     # Generated log files
├── exports/                  # Generated markdown reports
└── requirements.txt          # Dependencies
```

## 🔧 System Overview

**NewsItem Model** - Unified SQLAlchemy model with business logic and persistence
**Content Fetcher** - High-performance extraction with domain blacklisting
**TLDR Scraper** - Main orchestrator coordinating all operations
**Database Manager** - Robust SQLite operations with duplicate detection
**Logging System** - Multi-level logging with file rotation and performance metrics
**Daily Aggregation** - Main execution script with progress visualization

## ⚙️ Performance Optimizations

### Domain Blacklisting
```python
BLACKLISTED_DOMAINS = {'minihf.com'}  # Skip slow/problematic domains
```

### Timeout Management
- Connection timeout: 8 seconds
- Read timeout: 8 seconds  
- Retry attempts: 2
- Intelligent fallback to summaries

## � Sample Output

```
📄 Full content fetching enabled (with domain blacklisting for speed)
🔍 Step 1/5: Checking existing database content... ✅
📰 Step 2/5: Scraping latest AI news... ✅ Found 8 articles
📄 Step 3/5: Fetching full article content... ✅ 6/8 with content
💾 Step 4/5: Saving to database... ✅ Saved: 3, Duplicates: 5
📝 Step 5/5: Exporting to markdown... ✅ Exported to: exports/tldr_ai_news_2025-07-27.md
```

## �️ Database & Export

**Database Schema**: SQLite with NewsItem model including content hashing for deduplication
**Export Format**: Professional markdown reports with statistics and categorized content
**Duplicate Detection**: URL matching, content hashing, and title similarity

## �️ Development

```bash
# Requirements
Python 3.8+
Dependencies: requests, beautifulsoup4, sqlalchemy, tqdm

# Key Files
src/aggregation/        # Core module (see module README)
scripts/daily_aggregation.py  # Main CLI entry point
requirements.txt        # All dependencies
```

## � Advanced Features

- **🔄 Intelligent Retry Logic**: 2-attempt retry with exponential backoff
- **📊 Progress Tracking**: Real-time tqdm progress bars
- **🛡️ Error Resilience**: Graceful fallbacks to TLDR summaries
- **⚡ Performance Monitoring**: Built-in timing and statistics
- **🔍 Debug Support**: Comprehensive logging and error reporting

## � Troubleshooting

**Slow Performance**: Check network connectivity, consider adding domains to blacklist
**Missing Content**: Verify URLs are accessible, check if domains are blacklisted
**Database Issues**: Ensure SQLite permissions and disk space

## 📄 License

MIT License - see LICENSE file for details.

## 🤝 Contributing

1. Fork repository
2. Create feature branch  
3. Add tests if applicable
4. Submit pull request

For detailed technical documentation, see `src/aggregation/README.md`
