# College Website Data Extraction System

A comprehensive system for crawling college websites and extracting structured information about admissions, placements, and internships using AI-powered data extraction.

## System Architecture

This system combines traditional web crawling with AI-powered data extraction to collect and structure information from college websites. The architecture consists of:

1. **Intelligent Crawler**: Uses Playwright for browser automation to navigate websites and handle JavaScript-heavy pages
2. **Multi-format Extractor**: Processes various content types (HTML, tables, images, PDFs)
3. **AI Processing Engine**: Integrates with Hugging Face-hosted AI models for intelligent data extraction
4. **MongoDB Storage**: Stores both raw and structured data
5. **Anti-Crawling Measures**: Implements human-like browsing behavior to avoid detection

## Setup Instructions

### Prerequisites

- Python 3.9+
- MongoDB
- Hugging Face account with deployed AI models (or use our pre-deployed endpoint)

### Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/college-data-crawler.git
   cd college-data-crawler
   ```

2. Create and activate a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Setup environment variables:
   ```
   cp .env.example .env
   ```
   Edit the `.env` file to configure your MongoDB connection and other settings.

5. Install browser for Playwright:
   ```
   playwright install chromium
   ```

### Configuration

The system can be configured by editing the following files:

- `config/settings.py`: General configuration settings
- `config/targets.py`: Target college websites for crawling

You can also set environment variables in the `.env` file.

## Usage

### Crawling Websites

To start crawling all configured colleges:

```
python main.py
```

To crawl a specific college:

```
python main.py --college "Indian Institute of Technology Delhi"
```

To list available target colleges:

```
python main.py --list
```

### Processing Options

To only process previously crawled data (no new crawling):

```
python main.py --process-only
```

To disable browser automation and use requests only:

```
python main.py --no-browser
```

## Project Structure

```
college-data-crawler/
├── config/                 # Configuration files
│   ├── settings.py         # System settings
│   └── targets.py          # Target college definitions
├── crawler/                # Web crawling components
│   ├── browser.py          # Browser automation
│   ├── proxy.py            # Proxy management
│   └── crawler.py          # Main crawler engine
├── extractors/             # Content extraction
│   ├── base.py             # Base extractor
│   ├── admission.py        # Admission info extraction
│   ├── placement.py        # Placement info extraction
│   ├── pdf.py              # PDF processing
│   └── image.py            # Image processing
├── processors/             # AI processing
│   └── ai_processor.py     # Integration with AI models
├── storage/                # Data persistence
│   └── mongodb.py          # MongoDB connector
├── utils/                  # Utility functions
│   └── helpers.py          # Helper utilities
├── main.py                 # Main execution script
└── requirements.txt        # Dependencies
```

## AI Model Integration

This system integrates with the AI models hosted on Hugging Face Spaces for:

1. **Text Classification**: Identifying admission vs. placement content
2. **Named Entity Recognition**: Extracting key entities like dates, fees, courses
3. **Question Answering**: Extracting specific information based on queries
4. **OCR**: Converting images to text
5. **Chart Recognition**: Extracting data from visual charts

The AI endpoints are configured in `config/settings.py`.

## MongoDB Data Schema

The system stores data in two collections:

1. **Raw Data**: Stores the raw HTML content and metadata
2. **Processed Data**: Contains structured information extracted by the AI

The structure follows the schema defined in the project architecture document.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.