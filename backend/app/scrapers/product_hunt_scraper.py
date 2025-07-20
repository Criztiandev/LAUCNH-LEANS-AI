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
            
            # Extract additional details for top competitors
            for competitor in final_competitors[:5]:  # Only get details for top 5
                try:
                    await self._enrich_competitor_data(competitor)
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
                        if competitor:
                            competitors.append(competitor)
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
                name=name,
                description=description,
                website=external_link,  # Will be resolved later if needed
                estimated_users=estimated_users,
                estimated_revenue=None,  # Will be estimated later
                pricing_model=None,  # Will be enriched later
                source=self.source_name,
                source_url=source_url,
                confidence_score=0.8  # Higher confidence for structured data
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
        
        # Enrich with Product Hunt page data if we have a source URL
        if competitor.source_url:
            try:
                async with self.session.get(competitor.source_url) as response:
                    if response.status != 200:
                        return
                    
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
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
                        competitor.description = detailed_desc.get_text(strip=True)
                    
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
    
    def validate_config(self) -> bool:
        """
        Validate that the scraper is properly configured.
        
        Returns:
            True if configuration is valid, False otherwise
        """
        # Product Hunt scraper doesn't require API keys, just network access
        return True