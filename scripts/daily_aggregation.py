"""
Daily aggregation script for TLDR AI news
"""

import sys
import os
from datetime import datetime
from tqdm import tqdm
import time

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from aggregation.tldr_scraper import TLDRAIScraper
from aggregation.logging_config import setup_logging, get_logger, LoggedOperation, log_performance_metric

# Initialize logging
logger = setup_logging(log_level="INFO", log_to_file=True, log_to_console=True)


def daily_aggregation():
    """Run daily news aggregation with full content fetching"""
    start_time = time.time()
    
    print(f"Starting daily TLDR AI news aggregation - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("📄 Full content fetching enabled (with domain blacklisting for speed)")
    print("="*70)
    
    logger.info("="*50)
    logger.info("STARTING DAILY AGGREGATION")
    logger.info("="*50)
    
    # Always enable content fetching
    scraper = TLDRAIScraper(fetch_content=True)
    
    try:
        with LoggedOperation("daily_aggregation", logger):
            # Step 1: Check existing database content
            with LoggedOperation("database_check", logger):
                print("🔍 Step 1/5: Checking existing database content...")
                with tqdm(total=1, desc="Database check", bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt}") as pbar:
                    existing_items = scraper.db_manager.get_recent_news(days=7, source="TLDR AI")
                    print(f"   Database contains: {len(existing_items)} articles from last 7 days")
                    logger.info(f"Database check: Found {len(existing_items)} articles from last 7 days")
                    
                    if existing_items:
                        latest_date = max(item.published_date for item in existing_items)
                        print(f"   Latest article date in DB: {latest_date.strftime('%Y-%m-%d %H:%M')}")
                        logger.info(f"Latest article in DB: {latest_date.strftime('%Y-%m-%d %H:%M')}")
                    pbar.update(1)
            
            # Step 2: Scrape articles
            with LoggedOperation("article_scraping", logger):
                print("\n📰 Step 2/5: Scraping latest AI news...")
                with tqdm(total=3, desc="Scraping progress", bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt}") as pbar:
                    pbar.set_description("Fetching TLDR homepage")
                    news_collection = scraper.scrape_ai_news()
                    pbar.update(1)
                    
                    if not news_collection.items:
                        print("   No new articles found (all are duplicates)")
                        logger.info("No new articles found - all are duplicates")
                        return
                    
                    pbar.set_description("Extracting articles")
                    pbar.update(1)
                    
                    pbar.set_description("Processing content")
                    pbar.update(1)
                
                print(f"   ✅ Found {len(news_collection.items)} articles")
                logger.info(f"Scraping completed: Found {len(news_collection.items)} articles")
        
            # Step 3: Fetch full article content
            with LoggedOperation("content_fetching", logger):
                print("\n📄 Step 3/5: Fetching full article content...")
                articles_with_content = 0
                total_words = 0
                
                with tqdm(total=len(news_collection.items), desc="Content fetching", 
                          bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} articles") as pbar:
                    for item in news_collection.items:
                        if item.content:
                            articles_with_content += 1
                            total_words += len(item.content.split())
                        pbar.set_description(f"Content fetched: {articles_with_content}/{len(news_collection.items)}")
                        pbar.update(1)
                        time.sleep(0.1)  # Small delay to show progress
                
                print(f"   ✅ Articles with content: {articles_with_content}/{len(news_collection.items)}")
                print(f"   ✅ Total words extracted: {total_words:,}")
                print(f"   🚫 Blacklisted domains skipped for faster processing")
                logger.info(f"Content fetching completed: {articles_with_content}/{len(news_collection.items)} articles with content, {total_words:,} words")
        
            # Step 4: Save to database
            with LoggedOperation("database_save", logger):
                print("\n💾 Step 4/5: Saving to database...")
                with tqdm(total=len(news_collection.items), desc="Saving articles", 
                          bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} processed") as pbar:
                    stats = scraper.save_to_database(news_collection)
                    pbar.update(len(news_collection.items))
                
                print(f"   ✅ Saved: {stats['saved']} articles")
                print(f"   🔄 Duplicates: {stats['duplicates']}")
                print(f"   ❌ Errors: {stats['errors']}")
                logger.info(f"Database save completed: {stats['saved']} saved, {stats['duplicates']} duplicates, {stats['errors']} errors")
                
                # Show duplicate breakdown for debugging
                if stats['duplicates'] > 0 and stats.get('duplicate_reasons'):
                    print(f"   📊 Duplicate breakdown:")
                    for reason, count in stats['duplicate_reasons'].items():
                        print(f"     - {reason.replace('_', ' ').title()}: {count}")
                
                # If all are duplicates, show some examples
                if stats['saved'] == 0 and stats['duplicates'] > 0:
                    print(f"\n   🔍 DEBUG: All articles were duplicates. Checking why...")
                    with tqdm(total=min(3, len(news_collection.items)), desc="Analyzing duplicates", 
                              bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} checked") as pbar:
                        for i, item in enumerate(news_collection.items[:3], 1):
                            is_dup, reason = scraper.db_manager.is_duplicate(item)
                            print(f"   {i}. '{item.title[:60]}...' -> {reason}")
                            pbar.update(1)
                            time.sleep(0.2)
        
            # Step 5: Export to markdown
            with LoggedOperation("markdown_export", logger):
                print("\n📝 Step 5/5: Exporting to markdown...")
                with tqdm(total=1, desc="Creating markdown", bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt}") as pbar:
                    filename = scraper.export_to_markdown(news_collection)
                    pbar.update(1)
                print(f"   ✅ Exported to: {filename}")
                logger.info(f"Markdown export completed: {filename}")
        
        # Final summary
        total_duration = time.time() - start_time
        print("\n" + "="*70)
        print("🎉 DAILY AGGREGATION SUMMARY:")
        print("="*70)
        
        print(f"  • Total articles found: {len(news_collection.items)}")
        print(f"  • New articles saved: {stats['saved']}")
        print(f"  • Articles with content: {articles_with_content}")
        print(f"  • Total words scraped: {total_words:,}")
        print(f"  • Export file created: ✅")
        print(f"  • Total runtime: {total_duration:.1f} seconds")
        
        if news_collection.items:
            print(f"\n📰 Latest articles processed:")
            for i, item in enumerate(news_collection.items[:5], 1):
                word_count = len(item.content.split()) if item.content else 0
                print(f"  {i}. {item.title} ({word_count:,} words)")
        
        print(f"\n✅ Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"Daily aggregation completed successfully in {total_duration:.1f} seconds")
        
    except Exception as e:
        print(f"❌ Error during daily aggregation: {e}")
        logger.error(f"Daily aggregation failed: {e}")
        import traceback
        traceback.print_exc()
        logger.error(f"Full traceback: {traceback.format_exc()}")
    
    finally:
        scraper.close()


if __name__ == "__main__":
    daily_aggregation()
