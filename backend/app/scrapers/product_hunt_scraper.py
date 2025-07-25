"""
Product Hunt scraper for extracting competitor data and product information.
"""
import asyncio
import logging
from typing import List, Dict, Any, Optional
from urllib.parse import quote_plus, urljoin
import re

import aiohttp
from bs4 import BeautifulSoup

from .base_scraper import BaseScraper, ScrapingResult, ScrapingStatus, CompetitorData, FeedbackData
from ..utils.data_cleaner import DataCleaner
from ..services.sentiment_analysis_service import SentimentAnalysisService


logger = logging.getLogger(__name__)


class ProductHuntScraper(BaseScraper):
    """Scraper for Product Hunt to extract competitor and product data."""
    
    def __init__(self):
        """Initialize the Product Hunt scraper."""
        super().__init__("Product Hunt")
        self.base_url = "https://www.producthunt.com"
        self.search_url = f"{self.base_url}/search"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        self.session: Optional[aiohttp.ClientSession] = None
        self.sentiment_analyzer = SentimentAnalysisService()
        self.max_comments_per_product = 10  # Increased to capture more pain points
    
    async def scrape(self, keywords: List[str], idea_text: str) -> ScrapingResult:
        """
        Scrape Product Hunt for competitor data based on keywords.
        
        Args:
            keywords: List of extracted keywords from the idea
            idea_text: Original idea text for context
            
        Returns:
            ScrapingResult containing competitors and feedback data
        """
        try:
            # Store keywords for relevance checking
            self.search_keywords = [kw.lower() for kw in keywords]
            
            competitors = []
            feedback = []
            
            # Create session if not exists
            if not self.session:
                timeout = aiohttp.ClientTimeout(total=self.timeout)
                self.session = aiohttp.ClientSession(
                    headers=self.headers,
                    timeout=timeout
                )
            
            # Search for each keyword
            for keyword in keywords[:3]:  # Limit to top 3 keywords to avoid rate limiting
                try:
                    keyword_competitors = await self._search_products(keyword)
                    competitors.extend(keyword_competitors)
                    
                    # Add small delay between searches to be respectful
                    await asyncio.sleep(1)
                    
                except Exception as e:
                    logger.warning(f"Failed to search for keyword '{keyword}': {str(e)}")
                    continue
            
            # Remove duplicates based on name
            unique_competitors = self._deduplicate_competitors(competitors)
            
            # Limit results to avoid overwhelming the system
            final_competitors = unique_competitors[:10]
            
            # Initialize comments and sentiment_summary for all competitors
            for competitor in final_competitors:
                # Set default empty values for all competitors
                await self._add_comments_to_competitor(competitor, [])
            
            # Extract additional details and comments for top competitors
            for competitor in final_competitors[:5]:  # Only get details for top 5
                try:
                    await self._enrich_competitor_data(competitor)
                    
                    # Extract comments for this competitor with sentiment analysis
                    competitor_comments = await self._extract_comments_with_sentiment(competitor)
                    
                    # Update with actual comments and sentiment summary
                    await self._add_comments_to_competitor(competitor, competitor_comments)
                    
                    # Also add to feedback for backward compatibility
                    competitor_feedback = await self._extract_comments(competitor)
                    feedback.extend(competitor_feedback)
                    
                    await asyncio.sleep(0.5)  # Small delay between requests
                except Exception as e:
                    logger.warning(f"Failed to enrich data for {competitor.name}: {str(e)}")
                    continue
            
            status = ScrapingStatus.SUCCESS if final_competitors else ScrapingStatus.FAILED
            
            return ScrapingResult(
                status=status,
                competitors=final_competitors,
                feedback=feedback,
                metadata={
                    "keywords_searched": keywords[:3],
                    "total_found": len(final_competitors),
                    "source": self.source_name
                }
            )
            
        except Exception as e:
            logger.error(f"Product Hunt scraping failed: {str(e)}")
            return ScrapingResult(
                status=ScrapingStatus.FAILED,
                competitors=[],
                feedback=[],
                error_message=str(e)
            )
        finally:
            if self.session:
                await self.session.close()
                self.session = None
    
    async def _search_products(self, keyword: str) -> List[CompetitorData]:
        """
        Search for products on Product Hunt using a keyword.
        
        Args:
            keyword: Search keyword
            
        Returns:
            List of CompetitorData objects
        """
        competitors = []
        
        try:
            # Construct search URL
            search_params = f"?q={quote_plus(keyword)}"
            url = f"{self.search_url}{search_params}"
            
            async with self.session.get(url) as response:
                if response.status != 200:
                    logger.warning(f"Search request failed with status {response.status}")
                    return competitors
                
                html = await response.text()
                
                # Product Hunt now uses React with embedded JSON data
                # Try to extract product data from the embedded JSON
                json_competitors = self._extract_from_json_data(html, keyword)
                if json_competitors:
                    competitors.extend(json_competitors)
                else:
                    # Fallback to HTML parsing if JSON extraction fails
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Find product cards using the specific Product Hunt class structure
                    product_cards = soup.find_all('div', class_='styles_item__Dk_nz')
                    
                    if not product_cards:
                        # Try alternative selectors for different page layouts
                        product_cards = soup.find_all(['div', 'article'], class_=re.compile(r'.*product.*|.*item.*'))
                        
                    if not product_cards:
                        # Fallback to generic post links
                        product_cards = soup.find_all('a', href=re.compile(r'/posts/'))
                    
                    for card in product_cards[:8]:  # Limit to 8 results per keyword
                        try:
                            competitor = self._extract_competitor_from_card(card, keyword)
                            if competitor and self._is_product_relevant(competitor):
                                competitors.append(competitor)
                            elif competitor:
                                logger.debug(f"Skipping irrelevant product: {competitor.name}")
                        except Exception as e:
                            logger.debug(f"Failed to extract competitor from card: {str(e)}")
                            continue
                        
        except Exception as e:
            logger.error(f"Failed to search products for keyword '{keyword}': {str(e)}")
        
        return competitors
    
    def _extract_competitor_from_card(self, card, keyword: str) -> Optional[CompetitorData]:
        """
        Extract competitor data from a product card element.
        
        Args:
            card: BeautifulSoup element representing a product card
            keyword: The search keyword used
            
        Returns:
            CompetitorData object or None if extraction fails
        """
        try:
            # Extract name using Product Hunt's specific structure
            name_element = card.find('a', class_='styles_title__HzPeb')
            if not name_element:
                # Fallback to generic selectors
                name_element = (
                    card.find(['h1', 'h2', 'h3', 'h4'], class_=re.compile(r'.*title.*|.*name.*')) or
                    card.find('a', href=re.compile(r'/posts/')) or
                    card.find(string=re.compile(r'\w+'))
                )
            
            if not name_element:
                return None
            
            name = name_element.get_text(strip=True) if hasattr(name_element, 'get_text') else str(name_element).strip()
            
            if not name or len(name) < 2:
                return None
            
            # Extract description using Product Hunt's specific structure
            description_element = card.find('div', class_='color-lighter-grey fontSize-mobile-12 fontSize-desktop-16 fontSize-tablet-16 fontSize-widescreen-16 fontWeight-400 noOfLines-2')
            if not description_element:
                # Fallback to generic selectors
                description_element = (
                    card.find(['p', 'div'], class_=re.compile(r'.*description.*|.*tagline.*')) or
                    card.find('p')
                )
            description = description_element.get_text(strip=True) if description_element else None
            
            # Extract Product Hunt URL
            producthunt_anchor = card.find('a', {'href': True, 'aria-label': name})
            source_url = None
            if producthunt_anchor and producthunt_anchor.get('href'):
                source_url = urljoin(self.base_url, producthunt_anchor['href'])
            elif card.find('a', href=re.compile(r'/posts/')):
                link_element = card.find('a', href=re.compile(r'/posts/'))
                source_url = urljoin(self.base_url, link_element['href'])
            
            # Extract upvotes using Product Hunt's specific structure
            upvotes_div = card.find('div', class_='color-lighter-grey fontSize-12 fontWeight-600 noOfLines-undefined')
            estimated_users = None
            if upvotes_div:
                upvotes_text = upvotes_div.get_text(strip=True).replace(',', '')
                vote_match = re.search(r'(\d+)', upvotes_text)
                if vote_match:
                    votes = int(vote_match.group(1))
                    # Rough estimation: votes * 10 for estimated users
                    estimated_users = votes * 10
            else:
                # Fallback to generic vote selectors
                vote_element = card.find(string=re.compile(r'\d+')) or card.find(['span', 'div'], class_=re.compile(r'.*vote.*|.*upvote.*'))
                if vote_element:
                    vote_text = vote_element.get_text(strip=True) if hasattr(vote_element, 'get_text') else str(vote_element)
                    vote_match = re.search(r'(\d+)', vote_text)
                    if vote_match:
                        votes = int(vote_match.group(1))
                        estimated_users = votes * 10
            
            # Extract external product link
            external_link = None
            link_anchor = card.find('a', class_='styles_externalLinkIcon__vjPDi')
            if link_anchor and link_anchor.get('href'):
                external_link = urljoin(self.base_url, link_anchor['href'])
            
            # Extract tags
            tag_anchors = card.find_all('a', class_='styles_underlinedLink__pq3Kl')
            tags = [tag.get_text(strip=True) for tag in tag_anchors]
            
            return CompetitorData(
                name=DataCleaner.clean_html_text(name),
                description=DataCleaner.clean_html_text(description),
                website=external_link,  # Will be resolved later if needed
                estimated_users=estimated_users,
                estimated_revenue=None,  # Will be estimated later
                pricing_model=None,  # Will be enriched later
                source=self.source_name,
                source_url=source_url,
                confidence_score=0.8,  # Higher confidence for structured data
                comments=[],  # Initialize empty comments
                sentiment_summary=None  # Will be set later
            )
            
        except Exception as e:
            logger.debug(f"Failed to extract competitor data: {str(e)}")
            return None
    
    async def _enrich_competitor_data(self, competitor: CompetitorData) -> None:
        """
        Enrich competitor data by resolving external links and extracting additional info.
        
        Args:
            competitor: CompetitorData object to enrich
        """
        # First, resolve the external product link if we have a Product Hunt redirect
        if competitor.website and competitor.website.startswith(self.base_url):
            try:
                async with self.session.get(competitor.website) as response:
                    if response.status == 200:
                        # Follow redirects to get the actual product website
                        final_url = str(response.url)
                        if final_url.endswith('?ref=producthunt'):
                            final_url = final_url.rsplit('?ref=producthunt', 1)[0]
                        if not final_url.startswith(self.base_url):
                            competitor.website = final_url
            except Exception as e:
                logger.debug(f"Failed to resolve external link for {competitor.name}: {str(e)}")
        
        # Enrich with detailed Product Hunt page data if we have a source URL
        if competitor.source_url:
            try:
                async with self.session.get(competitor.source_url) as response:
                    if response.status != 200:
                        return
                    
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Extract structured data (JSON-LD) for detailed product info
                    await self._extract_structured_data(competitor, soup)
                    
                    # Try to find website link if we don't have one
                    if not competitor.website:
                        website_link = (
                            soup.find('a', href=re.compile(r'^https?://(?!.*producthunt).*')) or
                            soup.find('a', string=re.compile(r'website|visit|homepage', re.I))
                        )
                        
                        if website_link and website_link.get('href'):
                            href = website_link['href']
                            if href.startswith('http') and 'producthunt.com' not in href:
                                competitor.website = href
                    
                    # Try to extract more detailed description
                    detailed_desc = soup.find(['div', 'p'], class_=re.compile(r'.*description.*|.*detail.*'))
                    if detailed_desc and len(detailed_desc.get_text(strip=True)) > len(competitor.description or ""):
                        competitor.description = DataCleaner.clean_html_text(detailed_desc.get_text(strip=True))
                    
            except Exception as e:
                logger.debug(f"Failed to enrich from Product Hunt page for {competitor.name}: {str(e)}")
        
        # Estimate revenue based on user count and typical SaaS metrics
        if competitor.estimated_users:
            if competitor.estimated_users > 10000:
                competitor.estimated_revenue = "$100K+ ARR"
            elif competitor.estimated_users > 5000:
                competitor.estimated_revenue = "$50K+ ARR"
            elif competitor.estimated_users > 1000:
                competitor.estimated_revenue = "$10K+ ARR"
            else:
                competitor.estimated_revenue = "Early stage"
        
        # Set basic pricing model assumption for SaaS products
        description_lower = (competitor.description or "").lower()
        if any(keyword in description_lower for keyword in ['saas', 'subscription', 'monthly', 'plan']):
            competitor.pricing_model = "Subscription"
        elif any(keyword in description_lower for keyword in ['free', 'open source']):
            competitor.pricing_model = "Freemium"
        else:
            competitor.pricing_model = "Unknown"
        
        # Increase confidence score for enriched data
        competitor.confidence_score = min(0.95, competitor.confidence_score + 0.15)
    
    async def _extract_comments_with_sentiment(self, competitor: CompetitorData) -> List[Dict[str, Any]]:
        """
        Extract comments with sentiment analysis for a Product Hunt product.
        
        Args:
            competitor: CompetitorData object with source_url
            
        Returns:
            List of comment dictionaries with sentiment analysis
        """
        comments = []
        
        if not competitor.source_url:
            return comments
        
        try:
            async with self.session.get(competitor.source_url) as response:
                if response.status != 200:
                    logger.debug(f"Failed to fetch comments page for {competitor.name}: {response.status}")
                    return comments
                
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                # Extract raw comments
                raw_comments = []
                
                # Try to extract comments from JSON data first
                json_comments = self._extract_comments_from_json(html)
                raw_comments.extend(json_comments)
                
                # If not enough comments from JSON, try HTML extraction
                if len(raw_comments) < self.max_comments_per_product:
                    html_comments = self._extract_comments_from_html(soup)
                    raw_comments.extend(html_comments)
                
                # Process and analyze sentiment for top comments
                for i, comment_data in enumerate(raw_comments[:self.max_comments_per_product]):
                    try:
                        comment_text = DataCleaner.clean_html_text(comment_data.get('text', ''))
                        if not comment_text or len(comment_text.strip()) < 10:
                            continue
                        
                        # Analyze sentiment
                        sentiment_result = self.sentiment_analyzer.analyze_sentiment(comment_text)
                        
                        comment_with_sentiment = {
                            'text': comment_text,
                            'author': DataCleaner.clean_html_text(comment_data.get('author', 'Anonymous')),
                            'sentiment': {
                                'label': sentiment_result.label.value,
                                'score': sentiment_result.score,
                                'confidence': sentiment_result.confidence
                            },
                            'position': i + 1
                        }
                        
                        comments.append(comment_with_sentiment)
                        
                    except Exception as e:
                        logger.debug(f"Failed to process comment: {str(e)}")
                        continue
                
                logger.info(f"Extracted {len(comments)} comments with sentiment for {competitor.name}")
                
        except Exception as e:
            logger.debug(f"Failed to extract comments with sentiment for {competitor.name}: {str(e)}")
        
        return comments
    
    async def _add_comments_to_competitor(self, competitor: CompetitorData, comments: List[Dict[str, Any]]) -> None:
        """
        Add comments and sentiment summary to competitor data, prioritizing pain points.
        
        Args:
            competitor: CompetitorData object to enhance
            comments: List of comments with sentiment analysis
        """
        # Categorize comments by sentiment - prioritize negative (pain points)
        negative_comments = []
        neutral_comments = []
        positive_comments = []
        
        for comment in comments:
            sentiment_label = comment.get('sentiment', {}).get('label', 'neutral')
            if sentiment_label == 'negative':
                negative_comments.append(comment)
            elif sentiment_label == 'positive':
                positive_comments.append(comment)
            else:
                neutral_comments.append(comment)
        
        # Sort negative comments by confidence (higher confidence pain points first)
        negative_comments.sort(key=lambda x: x.get('sentiment', {}).get('confidence', 0), reverse=True)
        
        # Prioritize comments: negative first (pain points), then neutral, then positive
        prioritized_comments = negative_comments + neutral_comments + positive_comments
        
        # Always set comments field with prioritized order
        competitor.comments = prioritized_comments if prioritized_comments else []
        
        if not comments:
            # Set empty sentiment summary if no comments
            competitor.sentiment_summary = {
                'total_comments': 0,
                'positive_count': 0,
                'negative_count': 0,
                'neutral_count': 0,
                'positive_percentage': 0.0,
                'negative_percentage': 0.0,
                'neutral_percentage': 0.0,
                'average_sentiment_score': 0.0,
                'overall_sentiment': 'neutral',
                'pain_points': [],
                'pain_point_categories': {},
                'positive_feedback': [],
                'neutral_feedback': []
            }
            return
        
        # Calculate sentiment summary with categorized feedback
        sentiment_labels = [comment['sentiment']['label'] for comment in comments]
        sentiment_scores = [comment['sentiment']['score'] for comment in comments]
        
        positive_count = sentiment_labels.count('positive')
        negative_count = sentiment_labels.count('negative')
        neutral_count = sentiment_labels.count('neutral')
        
        average_sentiment_score = sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0
        
        # Extract key pain points from negative comments
        pain_points = []
        for comment in negative_comments[:5]:  # Top 5 pain points
            pain_points.append({
                'text': comment['text'][:200] + '...' if len(comment['text']) > 200 else comment['text'],
                'author': comment.get('author', 'Anonymous'),
                'confidence': comment.get('sentiment', {}).get('confidence', 0)
            })
        
        # Categorize pain points by theme
        pain_point_categories = self._categorize_pain_points(negative_comments)
        
        # Extract positive feedback highlights
        positive_feedback = []
        for comment in positive_comments[:2]:  # Top 2 positive highlights
            positive_feedback.append({
                'text': comment['text'][:200] + '...' if len(comment['text']) > 200 else comment['text'],
                'author': comment.get('author', 'Anonymous'),
                'confidence': comment.get('sentiment', {}).get('confidence', 0)
            })
        
        # Extract neutral feedback
        neutral_feedback = []
        for comment in neutral_comments[:2]:  # Top 2 neutral comments
            neutral_feedback.append({
                'text': comment['text'][:200] + '...' if len(comment['text']) > 200 else comment['text'],
                'author': comment.get('author', 'Anonymous')
            })
        
        competitor.sentiment_summary = {
            'total_comments': len(comments),
            'positive_count': positive_count,
            'negative_count': negative_count,
            'neutral_count': neutral_count,
            'positive_percentage': round((positive_count / len(comments)) * 100, 1),
            'negative_percentage': round((negative_count / len(comments)) * 100, 1),
            'neutral_percentage': round((neutral_count / len(comments)) * 100, 1),
            'average_sentiment_score': round(average_sentiment_score, 3),
            'overall_sentiment': self._determine_overall_sentiment(average_sentiment_score),
            'pain_points': pain_points,  # Prioritized pain points
            'pain_point_categories': pain_point_categories,  # Categorized pain points
            'positive_feedback': positive_feedback,
            'neutral_feedback': neutral_feedback
        }
        
        logger.info(f"Added {len(comments)} comments to {competitor.name} - Pain points: {len(pain_points)}, Positive: {len(positive_feedback)}")
    
    def _determine_overall_sentiment(self, average_score: float) -> str:
        """
        Determine overall sentiment based on average score.
        
        Args:
            average_score: Average sentiment score
            
        Returns:
            Overall sentiment label
        """
        if average_score > 0.1:
            return 'positive'
        elif average_score < -0.1:
            return 'negative'
        else:
            return 'neutral'
    
    def _categorize_pain_points(self, negative_comments: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """
        Categorize pain points from negative comments into common themes.
        
        Args:
            negative_comments: List of negative comments
            
        Returns:
            Dictionary of categorized pain points
        """
        categories = {
            'usability': [],
            'performance': [],
            'features': [],
            'pricing': [],
            'support': [],
            'bugs': [],
            'other': []
        }
        
        # Keywords for categorization
        category_keywords = {
            'usability': ['confusing', 'difficult', 'hard to use', 'complicated', 'interface', 'ui', 'ux', 'navigation'],
            'performance': ['slow', 'crash', 'freeze', 'lag', 'loading', 'speed', 'performance', 'battery'],
            'features': ['missing', 'lack', 'need', 'want', 'feature', 'functionality', 'option'],
            'pricing': ['expensive', 'price', 'cost', 'money', 'subscription', 'payment', 'billing'],
            'support': ['support', 'help', 'customer service', 'response', 'contact'],
            'bugs': ['bug', 'error', 'broken', 'issue', 'problem', 'glitch', 'not working']
        }
        
        for comment in negative_comments:
            text = comment.get('text', '').lower()
            categorized = False
            
            for category, keywords in category_keywords.items():
                if any(keyword in text for keyword in keywords):
                    categories[category].append(comment.get('text', '')[:150])
                    categorized = True
                    break
            
            if not categorized:
                categories['other'].append(comment.get('text', '')[:150])
        
        # Remove empty categories
        return {k: v for k, v in categories.items() if v}
    
    
    def _extract_comments_from_html(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """
        Extract comments from HTML elements.
        
        Args:
            soup: BeautifulSoup object of the product page
            
        Returns:
            List of comment dictionaries
        """
        comments = []
        
        try:
            # Try to find comment containers with various selectors
            comment_elements = []
            
            # Pattern 1: Look for comment containers with specific classes
            comment_containers = soup.find_all(['div', 'article'], class_=re.compile(r'.*comment.*|.*review.*|.*feedback.*', re.I))
            comment_elements.extend(comment_containers)
            
            # Pattern 2: Look for user-generated content areas
            user_content = soup.find_all(['div', 'section'], class_=re.compile(r'.*user.*|.*discussion.*|.*conversation.*', re.I))
            comment_elements.extend(user_content)
            
            for element in comment_elements[:10]:  # Limit to 10 potential comments
                try:
                    comment_text = self._extract_comment_text(element)
                    if comment_text and len(comment_text.strip()) > 10:
                        
                        # Extract author info if available
                        author_element = element.find(['span', 'div', 'a'], class_=re.compile(r'.*author.*|.*user.*|.*name.*', re.I))
                        author = author_element.get_text(strip=True) if author_element else 'Anonymous'
                        
                        comments.append({
                            'text': comment_text.strip(),
                            'author': author
                        })
                        
                except Exception as e:
                    logger.debug(f"Failed to extract HTML comment: {str(e)}")
                    continue
                    
        except Exception as e:
            logger.debug(f"Failed to extract comments from HTML: {str(e)}")
        
        return comments
    
    async def _extract_comments(self, competitor: CompetitorData) -> List[FeedbackData]:
        """
        Extract comments from a Product Hunt product page.
        
        Args:
            competitor: CompetitorData object with source_url
            
        Returns:
            List of FeedbackData objects containing comments
        """
        comments = []
        
        if not competitor.source_url:
            return comments
        
        try:
            async with self.session.get(competitor.source_url) as response:
                if response.status != 200:
                    logger.debug(f"Failed to fetch comments page for {competitor.name}: {response.status}")
                    return comments
                
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                # Try to extract comments from various Product Hunt comment structures
                comment_elements = []
                
                # Pattern 1: Look for comment containers with specific classes
                comment_containers = soup.find_all(['div', 'article'], class_=re.compile(r'.*comment.*|.*review.*|.*feedback.*', re.I))
                comment_elements.extend(comment_containers)
                
                # Pattern 2: Look for structured comment data in JSON
                comment_data = self._extract_comments_from_json(html)
                if comment_data:
                    for comment_info in comment_data:
                        feedback_item = FeedbackData(
                            text=DataCleaner.clean_html_text(comment_info.get('text', '')),
                            source=self.source_name,
                            source_url=competitor.source_url,
                            author_info={
                                'product_name': DataCleaner.clean_html_text(competitor.name),
                                'author': DataCleaner.clean_html_text(comment_info.get('author', 'Anonymous')),
                                'comment_type': 'product_hunt_comment'
                            }
                        )
                        comments.append(feedback_item)
                
                # Pattern 3: Extract from HTML elements
                for element in comment_elements[:10]:  # Limit to 10 comments per product
                    try:
                        comment_text = self._extract_comment_text(element)
                        if comment_text and len(comment_text.strip()) > 10:  # Only meaningful comments
                            
                            # Extract author info if available
                            author_element = element.find(['span', 'div', 'a'], class_=re.compile(r'.*author.*|.*user.*|.*name.*', re.I))
                            author = author_element.get_text(strip=True) if author_element else 'Anonymous'
                            
                            feedback_item = FeedbackData(
                                text=DataCleaner.clean_html_text(comment_text.strip()),
                                source=self.source_name,
                                source_url=competitor.source_url,
                                author_info={
                                    'product_name': DataCleaner.clean_html_text(competitor.name),
                                    'author': DataCleaner.clean_html_text(author),
                                    'comment_type': 'product_hunt_comment'
                                }
                            )
                            comments.append(feedback_item)
                            
                    except Exception as e:
                        logger.debug(f"Failed to extract comment: {str(e)}")
                        continue
                
                logger.info(f"Extracted {len(comments)} comments for {competitor.name}")
                
        except Exception as e:
            logger.debug(f"Failed to extract comments for {competitor.name}: {str(e)}")
        
        return comments
    
    def _extract_comments_from_json(self, html: str) -> List[Dict[str, Any]]:
        """
        Extract comments from embedded JSON data in Product Hunt pages.
        
        Args:
            html: HTML content of the page
            
        Returns:
            List of comment dictionaries
        """
        comments = []
        
        try:
            import json
            
            # Look for comment data in various JSON patterns
            patterns = [
                r'"comments":\s*\[([^\]]*)\]',
                r'"reviews":\s*\[([^\]]*)\]',
                r'"feedback":\s*\[([^\]]*)\]'
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, html, re.DOTALL)
                for match in matches:
                    try:
                        # Try to parse the comment data
                        comment_json = f'[{match}]'
                        cleaned_json = comment_json.replace('undefined', 'null')
                        comment_data = json.loads(cleaned_json)
                        
                        for comment in comment_data:
                            if isinstance(comment, dict):
                                text = comment.get('text') or comment.get('body') or comment.get('content')
                                author = comment.get('author') or comment.get('user') or comment.get('name')
                                
                                if text and len(text.strip()) > 10:
                                    comments.append({
                                        'text': text.strip(),
                                        'author': author or 'Anonymous'
                                    })
                                    
                    except (json.JSONDecodeError, Exception) as e:
                        logger.debug(f"Failed to parse comment JSON: {str(e)}")
                        continue
            
            # Also look for individual comment objects
            comment_pattern = r'\{"text":"([^"]+)","author":"([^"]*)"[^}]*\}'
            comment_matches = re.findall(comment_pattern, html)
            
            for text, author in comment_matches:
                if len(text.strip()) > 10:
                    comments.append({
                        'text': text.strip(),
                        'author': author or 'Anonymous'
                    })
            
        except Exception as e:
            logger.debug(f"Failed to extract comments from JSON: {str(e)}")
        
        return comments[:10]  # Limit to 10 comments
    
    def _extract_comment_text(self, element) -> Optional[str]:
        """
        Extract comment text from a BeautifulSoup element.
        
        Args:
            element: BeautifulSoup element containing comment
            
        Returns:
            Comment text or None if extraction fails
        """
        try:
            # Try different approaches to extract comment text
            
            # Approach 1: Look for specific comment text elements
            text_elements = element.find_all(['p', 'div', 'span'], class_=re.compile(r'.*text.*|.*content.*|.*body.*', re.I))
            for text_elem in text_elements:
                text = text_elem.get_text(strip=True)
                if text and len(text) > 10:
                    return text
            
            # Approach 2: Get all text from the element, filtering out navigation/UI text
            all_text = element.get_text(strip=True)
            
            # Filter out common UI elements and short text
            if all_text and len(all_text) > 10:
                # Remove common UI text patterns
                ui_patterns = [
                    r'reply|like|share|report|delete|edit',
                    r'\d+\s*(likes?|replies?|hours?|days?|ago)',
                    r'show more|show less|read more'
                ]
                
                filtered_text = all_text
                for pattern in ui_patterns:
                    filtered_text = re.sub(pattern, '', filtered_text, flags=re.IGNORECASE)
                
                filtered_text = filtered_text.strip()
                if len(filtered_text) > 10:
                    return filtered_text
            
            return None
            
        except Exception as e:
            logger.debug(f"Failed to extract comment text: {str(e)}")
            return None
    
    async def _extract_structured_data(self, competitor: CompetitorData, soup: BeautifulSoup) -> None:
        """
        Extract additional data from JSON-LD structured data on the product page.
        
        Args:
            competitor: CompetitorData object to enrich
            soup: BeautifulSoup object of the product page
        """
        try:
            import json
            
            # Find JSON-LD scripts
            json_ld_scripts = soup.find_all('script', type='application/ld+json')
            
            for script in json_ld_scripts:
                try:
                    if not script.string:
                        continue
                        
                    structured_data = json.loads(script.string)
                    
                    # Handle both single objects and arrays
                    if isinstance(structured_data, list):
                        data_items = structured_data
                    else:
                        data_items = [structured_data]
                    
                    for item in data_items:
                        # Extract product information
                        if item.get('@type') in ['WebApplication', 'Product'] or (isinstance(item.get('@type'), list) and any(t in ['WebApplication', 'Product'] for t in item.get('@type', []))):
                            # Extract launch date
                            if 'datePublished' in item:
                                competitor.launch_date = item['datePublished'][:10]  # Just the date part
                            
                            # Extract founder/CEO information
                            if 'author' in item and isinstance(item['author'], list):
                                # Get the first author as the primary founder/CEO
                                if item['author']:
                                    first_author = item['author'][0]
                                    if isinstance(first_author, dict) and 'name' in first_author:
                                        competitor.founder_ceo = DataCleaner.clean_html_text(first_author['name'])
                            
                            # Extract rating information
                            if 'aggregateRating' in item:
                                rating_info = item['aggregateRating']
                                if 'ratingValue' in rating_info:
                                    competitor.average_rating = float(rating_info['ratingValue'])
                                if 'ratingCount' in rating_info:
                                    competitor.review_count = int(rating_info['ratingCount'])
                            
                            # Update description if we have a more detailed one
                            if 'description' in item and len(item['description']) > len(competitor.description or ""):
                                competitor.description = DataCleaner.clean_html_text(item['description'])
                        
                        # Extract review information
                        elif item.get('@type') == 'Review':
                            # Store the most helpful review (first one found, as they're usually sorted by helpfulness)
                            if not competitor.most_helpful_review and 'reviewBody' in item:
                                review_text = item['reviewBody']
                                if len(review_text) > 200:
                                    review_text = review_text[:200] + "..."
                                
                                # Add author name if available
                                if 'author' in item and isinstance(item['author'], dict) and 'name' in item['author']:
                                    author_name = DataCleaner.clean_html_text(item['author']['name'])
                                    review_text = f'"{review_text}" - {author_name}'
                                
                                competitor.most_helpful_review = DataCleaner.clean_html_text(review_text)
                            if 'reviewBody' in item and 'reviewRating' in item:
                                rating_value = item['reviewRating'].get('ratingValue', 0)
                                # Consider reviews with rating 4+ as potentially helpful
                                if rating_value >= 4:
                                    review_text = item['reviewBody']
                                    # Store the review if it's substantial (more than 50 characters)
                                    if len(review_text) > 50:
                                        competitor.most_helpful_review = DataCleaner.clean_html_text(review_text)
                
                except json.JSONDecodeError:
                    continue
                except Exception as e:
                    logger.debug(f"Failed to process structured data: {str(e)}")
                    continue
                    
        except Exception as e:
            logger.debug(f"Failed to extract structured data for {competitor.name}: {str(e)}")
    
    def _deduplicate_competitors(self, competitors: List[CompetitorData]) -> List[CompetitorData]:
        """
        Remove duplicate competitors based on name similarity.
        
        Args:
            competitors: List of CompetitorData objects
            
        Returns:
            Deduplicated list of competitors
        """
        unique_competitors = []
        seen_names = set()
        
        for competitor in competitors:
            # Normalize name for comparison
            normalized_name = competitor.name.lower().strip()
            
            # Skip if we've seen a very similar name
            is_duplicate = False
            for seen_name in seen_names:
                # Only consider exact matches or very similar names as duplicates
                if (normalized_name == seen_name or 
                    (len(normalized_name) > 5 and normalized_name in seen_name) or
                    (len(seen_name) > 5 and seen_name in normalized_name)):
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                unique_competitors.append(competitor)
                seen_names.add(normalized_name)
        
        return unique_competitors
    
    def _extract_from_json_data(self, html: str, keyword: str) -> List[CompetitorData]:
        """
        Extract product data from embedded JSON in Product Hunt's React app.
        
        Args:
            html: The HTML content containing embedded JSON
            keyword: The search keyword used
            
        Returns:
            List of CompetitorData objects
        """
        competitors = []
        
        try:
            import json
            
            # Look for the specific pattern we found in the debug output
            # The data is in: {"data":{"productSearch":{"edges":[...]}}}
            
            # Pattern 1: Extract the complete data object containing productSearch
            data_pattern = r'"data":\s*(\{"productSearch":\{"__typename":"ProductSearchConnection","edges":\[.*?\]\})'
            matches = re.findall(data_pattern, html, re.DOTALL)
            
            for match in matches:
                try:
                    # Add closing brace to complete the JSON
                    complete_json = match + '}'
                    # Clean up the JSON
                    cleaned_json = complete_json.replace('undefined', 'null')
                    
                    data = json.loads(cleaned_json)
                    
                    if 'productSearch' in data and 'edges' in data['productSearch']:
                        edges = data['productSearch']['edges']
                        logger.debug(f"Found {len(edges)} products in productSearch")
                        
                        for edge in edges:
                            if 'node' in edge:
                                product = edge['node']
                                competitor = self._extract_competitor_from_json_product(product, keyword)
                                if competitor:
                                    competitors.append(competitor)
                    
                except json.JSONDecodeError as e:
                    logger.debug(f"JSON decode error for data pattern: {str(e)}")
                    continue
                except Exception as e:
                    logger.debug(f"Failed to parse data pattern: {str(e)}")
                    continue
            
            # Pattern 2: If the above didn't work, try extracting individual products
            if not competitors:
                # Look for individual product nodes
                product_pattern = r'\{"__typename":"Product","id":"[^"]*","name":"([^"]*)","tagline":"([^"]*)","slug":"([^"]*)","reviewsRating":([^,]*),"reviewsCount":([^,]*)[^}]*\}'
                product_matches = re.findall(product_pattern, html)
                
                for match in product_matches:
                    try:
                        name, tagline, slug, rating, review_count = match
                        
                        # Create a pindow\[object
                        product = {
                            'name': name,
                            'tagline': tagline,
                            'slug': slug,
                            'reviewsRating': float(rating) if rating != 'null' else None,
                            'reviewsCount': int(review_count) if review_count != 'null' else None
                        }
                        
                        competitor = self._extract_competitor_from_json_product(product, keyword)
                        if competitor:
                            competitors.append(competitor)
                            
                    except Exception as e:
                        logger.debug(f"Failed to parse individual product: {str(e)}")
                        continue
            
            # Pattern 3: Try the Apollo SSR data transport as fallback
            if not competitors:
                apollo_pattern = r'"_R_[^"]*":\{"data":\{"productSearch":\{"__typename":"ProductSearchConnection","edges":\[([^\]]*)\]'
                apollo_matches = re.findall(apollo_pattern, html, re.DOTALL)
                
                for match in apollo_matches:
                    try:
                        # Parse the edges array content
                        edges_json = f'[{match}]'
                        cleaned_edges = edges_json.replace('undefined', 'null')
                        edges = json.loads(cleaned_edges)
                        
                        logger.debug(f"Found {len(edges)} products in Apollo data")
                        
                        for edge in edges:
                            if isinstance(edge, dict) and 'node' in edge:
                                product = edge['node']
                                competitor = self._extract_competitor_from_json_product(product, keyword)
                                if competitor:
                                    competitors.append(competitor)
                                    
                    except json.JSONDecodeError as e:
                        logger.debug(f"JSON decode error for Apollo pattern: {str(e)}")
                        continue
                    except Exception as e:
                        logger.debug(f"Failed to parse Apollo data: {str(e)}")
                        continue
                        
        except Exception as e:
            logger.debug(f"Failed to extract from JSON data: {str(e)}")
        
        logger.debug(f"Extracted {len(competitors)} competitors from JSON data")
        return competitors
    
    def _extract_competitor_from_json_product(self, product: Dict[str, Any], keyword: str) -> Optional[CompetitorData]:
        """
        Extract competitor data from a JSON product object.
        
        Args:
            product: JSON product object from Product Hunt API
            keyword: The search keyword used
            
        Returns:
            CompetitorData object or None if extraction fails
        """
        try:
            name = product.get('name', '').strip()
            if not name:
                return None
            
            description = product.get('tagline', '').strip()
            slug = product.get('slug', '')
            
            # Build Product Hunt URL
            source_url = f"{self.base_url}/posts/{slug}" if slug else None
            
            # Extract ratings as a proxy for popularity
            reviews_count = product.get('reviewsCount', 0)
            reviews_rating = product.get('reviewsRating', 0)
            
            # Estimate users based on reviews (reviews typically represent ~1-5% of users)
            estimated_users = None
            if reviews_count > 0:
                # Conservative estimate: each review represents ~50 users
                estimated_users = reviews_count * 50
            
            # Check if product is still online
            is_online = not product.get('isNoLongerOnline', False)
            
            return CompetitorData(
                name=DataCleaner.clean_html_text(name),
                description=DataCleaner.clean_html_text(description),
                website=None,  # Will be resolved later if needed
                estimated_users=estimated_users,
                estimated_revenue=None,  # Will be estimated later
                pricing_model=None,  # Will be enriched later
                source=self.source_name,
                source_url=source_url,
                confidence_score=0.9 if is_online else 0.6,  # Higher confidence for JSON data
                comments=[],  # Initialize empty comments
                sentiment_summary=None  # Will be set later
            )
            
        except Exception as e:
            logger.debug(f"Failed to extract competitor from JSON product: {str(e)}")
            return None
    
    def validate_config(self) -> bool:
        """
        Validate that the scraper is properly configured.
        
        Returns:
            True if configuration is valid, False otherwise
        """
        # Product Hunt scraper doesn't require API keys, just network access
        return True