import re
import html
import json
from typing import Dict, Any, List, Union


class DataCleaner:
    """Utility class for cleaning scraped data from HTML formatting and escape characters."""
    
    @staticmethod
    def clean_html_text(text: str) -> str:
        """
        Clean HTML tags and escape characters from text.
        
        Args:
            text: Raw text containing HTML tags and escape characters
            
        Returns:
            Cleaned plain text
        """
        if not text or not isinstance(text, str):
            return text
            
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        
        # Decode HTML entities
        text = html.unescape(text)
        
        # Replace common escape sequences
        text = text.replace('\\r\\n', '\n')
        text = text.replace('\\n', '\n')
        text = text.replace('\\r', '\n')
        text = text.replace('\\t', '\t')
        
        # Replace Unicode bullet points and other symbols
        text = text.replace('\\u2022', '•')
        text = text.replace('\\u2019', "'")
        text = text.replace('\\u201c', '"')
        text = text.replace('\\u201d', '"')
        text = text.replace('\\u2013', '–')
        text = text.replace('\\u2014', '—')
        text = text.replace('\\u00ae', '®')
        text = text.replace('\\u2122', '™')
        text = text.replace('\\u00a9', '©')
        
        # Clean up multiple whitespace and newlines
        text = re.sub(r'\n\s*\n', '\n\n', text)  # Multiple newlines to double newline
        text = re.sub(r'[ \t]+', ' ', text)  # Multiple spaces/tabs to single space
        text = text.strip()
        
        return text
    
    @staticmethod
    def clean_data_recursively(data: Union[Dict, List, str, Any]) -> Union[Dict, List, str, Any]:
        """
        Recursively clean all string values in a data structure.
        
        Args:
            data: Data structure (dict, list, or primitive) to clean
            
        Returns:
            Cleaned data structure
        """
        if isinstance(data, dict):
            return {key: DataCleaner.clean_data_recursively(value) for key, value in data.items()}
        elif isinstance(data, list):
            return [DataCleaner.clean_data_recursively(item) for item in data]
        elif isinstance(data, str):
            return DataCleaner.clean_html_text(data)
        else:
            return data
    
    @staticmethod
    def clean_json_file(input_file: str, output_file: str = None) -> None:
        """
        Clean HTML formatting from a JSON file.
        
        Args:
            input_file: Path to input JSON file
            output_file: Path to output JSON file (defaults to input_file if not provided)
        """
        if output_file is None:
            output_file = input_file
            
        try:
            with open(input_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            cleaned_data = DataCleaner.clean_data_recursively(data)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(cleaned_data, f, indent=2, ensure_ascii=False)
                
            print(f"Successfully cleaned data and saved to {output_file}")
            
        except Exception as e:
            print(f"Error cleaning JSON file: {str(e)}")
            raise


if __name__ == "__main__":
    # Example usage
    cleaner = DataCleaner()
    
    # Test with sample text
    sample_text = "<h2><b>Everything you love about WhatsApp plus built-in tools for business</b></h2> WhatsApp Business is a free-to-download app with built-in tools to help you work smarter, build trust, and grow your business. \\r\\n\\r\\nYou get  free calls* and free international messaging* plus business features to help you do more with conversations.\\r\\n\\r\\n\\r\\n<h2><b>Download the app to get business benefits like these:</b></h2>\\r\\n\\u2022 <b>Work smarter</b>. Save time by letting the app do the work for you!"
    
    cleaned = cleaner.clean_html_text(sample_text)
    print("Original:", sample_text)
    print("Cleaned:", cleaned)