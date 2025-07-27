# TrendCreate

TrendCreate is an AI-powered automation tool that helps content creators generate 1-minute tech trend videos end-to-end — from news aggregation to scriptwriting, voice cloning, digital avatar generation, and asset packaging, all ready for editing and publishing.

## Core Features

🔍 **Content Aggregation** - Collect trending AI/tech news from multiple sources  
✍️ **Script Generator** - Create short-form scripts in Chinese & English  
🗣️ **Voice Cloning** - Generate natural voiceovers using AI voice clones  
🧍‍♀️ **Digital Avatar** - Create talking head videos with your AI avatar  
🎞️ **B-roll Generator** - Auto-find relevant stock videos and images  
📁 **Asset Export** - Package everything for easy video editing  
📱 **Multi-Platform** - Optimize content for Xiaohongshu, TikTok, YouTube

## Current Status

✅ **Content Aggregation** - Working (TLDR AI scraper)  
🚧 **Script Generator** - In development  
🚧 **Voice Cloning** - Planned  
🚧 **Digital Avatar** - Planned  
🚧 **B-roll Generator** - Planned  
🚧 **Asset Export** - Planned  
🚧 **Multi-Platform** - Planned

## Quick Start (Current Features)

```bash
# Install dependencies
pip install -r requirements.txt

# Run news aggregation
python scripts/daily_aggregation.py
```

## Requirements

- Python 3.8+
- Internet connection

## Project Structure

```
TrendCreate/
├── scripts/daily_aggregation.py  # News aggregation (working)
├── src/
│   ├── aggregation/              # Content collection
│   ├── scriptgen/                # Script generation (planned)
│   ├── voice/                    # Voice cloning (planned)
│   ├── avatar/                   # Digital avatar (planned)
│   ├── broll/                    # B-roll assets (planned)
│   ├── shorts/                   # Video generation (planned)
│   ├── planner/                  # Content planning (planned)
│   └── post/                     # Publishing tools (planned)
├── data/                         # Database files
├── exports/                      # Generated content
└── logs/                         # Log files
```

## Vision

Transform tech news into engaging short-form videos with minimal manual work - perfect for content creators targeting Chinese and English audiences on platforms like Xiaohongshu, TikTok, and YouTube.
