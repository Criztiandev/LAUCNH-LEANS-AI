# Data Cleaning Utilities

This module provides utilities for cleaning scraped data from HTML formatting and escape characters.

## Overview

When scraping data from app stores and other web sources, the raw data often contains:
- HTML tags (`<h2>`, `<b>`, `<i>`, etc.)
- Escape sequences (`\r\n`, `\n`, `\t`)
- Unicode characters (`\u2022`, `\u2019`, etc.)
- Multiple whitespace and formatting issues

The `DataCleaner` class provides methods to clean this data into readable, plain text format.

## Features

### HTML Tag Removal
- Removes all HTML tags while preserving the text content
- Handles nested tags and malformed HTML gracefully

### Escape Sequence Conversion
- Converts `\r\n` and `\n` to proper newlines
- Handles tab characters (`\t`)
- Preserves intentional formatting

### Unicode Character Conversion
- Converts common Unicode characters to their readable equivalents:
  - `\u2022` → `•` (bullet point)
  - `\u2019` → `'` (apostrophe)
  - `\u201c` → `"` (left double quote)
  - `\u201d` → `"` (right double quote)
  - `\u2013` → `–` (en dash)
  - `\u2014` → `—` (em dash)
  - `\u00ae` → `®` (registered trademark)
  - `\u2122` → `™` (trademark)
  - `\u00a9` → `©` (copyright)

### Whitespace Normalization
- Converts multiple consecutive spaces/tabs to single spaces
- Converts multiple newlines to double newlines for readability
- Trims leading and trailing whitespace

## Usage

### Basic Text Cleaning

```python
from app.utils.data_cleaner import DataCleaner

# Clean a single text string
raw_text = "<h2><b>App Title</b></h2>\\r\\n\\u2022 Feature 1"
clean_text = DataCleaner.clean_html_text(raw_text)
print(clean_text)  # Output: "App Title\n• Feature 1"
```

### Recursive Data Structure Cleaning

```python
# Clean all strings in a complex data structure
data = {
    'name': '<b>WhatsApp Business</b>',
    'description': '<h2>Features:</h2>\\r\\n\\u2022 Work smarter',
    'competitors': [
        {
            'name': '<i>Meta Business Suite</i>',
            'reviews': [
                {'text': 'Great app!\\r\\n\\r\\nHighly recommended.'}
            ]
        }
    ]
}

cleaned_data = DataCleaner.clean_data_recursively(data)
```

### JSON File Cleaning

```python
# Clean an entire JSON file
DataCleaner.clean_json_file('input.json', 'output.json')

# Clean in place (overwrites original file)
DataCleaner.clean_json_file('data.json')
```

### Command Line Usage

```bash
# Clean a JSON file with backup
python clean_scraped_data.py input.json --backup

# Clean with custom output file
python clean_scraped_data.py input.json -o cleaned_output.json
```

## Integration with Scrapers

The data cleaning is automatically integrated into all scrapers:

- **Google Play Store Scraper**: Cleans app descriptions, names, and review text
- **App Store Scraper**: Cleans iOS app data and reviews
- **Microsoft Store Scraper**: Cleans Windows app information

This ensures that all scraped data is automatically cleaned before being saved to JSON files.

## Example: Before and After

### Before Cleaning
```
<h2><b>Everything you love about WhatsApp plus built-in tools for business</b></h2> WhatsApp Business is a free-to-download app\\r\\n\\r\\n\\u2022 <b>Work smarter</b>. Save time by letting the app do the work for you!
```

### After Cleaning
```
Everything you love about WhatsApp plus built-in tools for business WhatsApp Business is a free-to-download app

• Work smarter. Save time by letting the app do the work for you!
```

## Testing

Run the test suite to verify data cleaning functionality:

```bash
python test_data_cleaning.py
```

Run the demo to see cleaning in action:

```bash
python demo_cleaning.py
```

## Error Handling

The data cleaner is designed to be robust:
- Handles `None` values gracefully
- Preserves non-string data types
- Continues processing even if individual items fail
- Logs errors for debugging without stopping the cleaning process

## Performance

The data cleaner is optimized for:
- Large JSON files with thousands of entries
- Nested data structures of arbitrary depth
- Memory-efficient processing
- Fast regex-based cleaning operations