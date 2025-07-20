"""
Google search scraper for extracting competitor information and market trends.
"""
import asyncio
import logging
import os
import re
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
import random
from urllib.parse import quote_plus, urlparse

import aiohttp
from bs4 import BeautifulSoup

from .base_scraper import BaseScraper, ScrapingResult, ScrapingStatus, CompetitorData, FeedbackData


logger = logging.getLogger(__name__)


class GoogleScraper(BaseScraper):
    """Scraper for Google search to extract competitor information and market trends."""
    
    def __init__(self):
        """Initialize the Google scraper."""
        super().__init__("Google")
        self.base_url = "https://www.google.com/search"
        self.num_results = 10
        self.timeout = 30
        self.max_retries = 3
        self.delay_between_requests = 2  # seconds
        
        # User agents to rotate for avoiding bot detection
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.1 Safari/605.1.15",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:95.0) Gecko/20100101 Firefox/95.0",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.45 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.55 Safari/537.36"
        ]
        
        # Proxy configuration (optional)
        self.proxy = os.getenv('GOOGLE_SCRAPER_PROXY')
    
    def validate_config(self) -> bool:
        """
        Validate that the Google scraper is properly configured.
        
        Returns:
            True if configuration is valid, False otherwise
        """
        try:
            # Check if we have valid user agents
            if not self.user_agents or len(self.user_agents) == 0:
                logger.error("No user agents configured for Google scraper")
                return False
            
            # Check if base URL is valid
            if not self.base_url or not self.base_url.startswith('http'):
                logger.error("Invalid base URL for Google scraper")
                return False
            
            # Check timeout and retry settings
            if self.timeout <= 0 or self.max_retries <= 0:
                logger.error("Invalid timeout or retry settings for Google scraper")
                return False
            
            # All checks passed
            logger.info("Google scraper configuration is valid")
            return True
            
        except Exception as e:
            logger.error(f"Google scraper configuration validation failed: {str(e)}")
            return False
    
    async def scrape(self, keywords: List[str], idea_text: str) -> ScrapingResult:
        """
        Scrape Google search for competitor information and market trends.
        
        Args:
            keywords: List of extracted keywords from the idea
            idea_text: Original idea text for context
            
        Returns:
            ScrapingResult containing competitor data and market trends
        """
        try:
            competitors = []
            feedback = []
            metadata = {
                "keywords_searched": [],
                "search_queries": [],
                "successful_queries": 0,
                "failed_queries": 0,
                "source": self.source_name
            }
            
            # Generate search queries based on keywords and idea text
            search_queries = self._generate_search_queries(keywords, idea_text)
            metadata["search_queries"] = search_queries
            
            # Execute searches for each query
            for query in search_queries[:5]:  # Limit to top 5 queries to avoid rate limiting
                try:
                    search_results = await self._execute_search(query)
                    
                    # Extract competitor information
                    query_competitors = self._extract_competitors(search_results, query)
                    competitors.extend(query_competitors)
                    
                    # Extract market feedback
                    query_feedback = self._extract_feedback(search_results, query)
                    feedback.extend(query_feedback)
                    
                    metadata["successful_queries"] += 1
                    metadata["keywords_searched"].append(query)
                    
                    # Add delay between requests to avoid rate limiting
                    await asyncio.sleep(self.delay_between_requests)
                    
                except Exception as e:
                    logger.warning(f"Failed to execute Google search for query '{query}': {str(e)}")
                    metadata["failed_queries"] += 1
                    continue
            
            # Remove duplicate competitors based on name
            unique_competitors = self._deduplicate_competitors(competitors)
            
            # Remove duplicate feedback
            unique_feedback = self._deduplicate_feedback(feedback)
            
            # Determine scraping status
            if metadata["successful_queries"] > 0:
                status = ScrapingStatus.SUCCESS if len(unique_competitors) > 0 else ScrapingStatus.PARTIAL_SUCCESS
            else:
                status = ScrapingStatus.FAILED
            
            # Update metadata
            metadata.update({
                "total_competitors": len(unique_competitors),
                "total_feedback": len(unique_feedback)
            })
            
            # If we didn't find any competitors, just return an empty array
            # We don't want to return mock data as it would be inaccurate
            if not unique_competitors:
                logger.warning("No competitors found from Google search results")
                # Keep status as is - it will be FAILED if no successful queries, otherwise PARTIAL_SUCCESS
            
            return ScrapingResult(
                status=status,
                competitors=unique_competitors[:15],  # Limit to top 15 competitors
                feedback=unique_feedback[:20],  # Limit to top 20 feedback items
                metadata=metadata
            )
            
        except Exception as e:
            logger.error(f"Google scraping failed: {str(e)}")
            return ScrapingResult(
                status=ScrapingStatus.FAILED,
                competitors=[],
                feedback=[],
                error_message=str(e)
            )
    
    def _generate_search_queries(self, keywords: List[str], idea_text: str) -> List[str]:
        """
        Generate search queries based on keywords and idea text.
        
        Args:
            keywords: List of keywords extracted from the idea
            idea_text: Original idea text
            
        Returns:
            List of search queries
        """
        # Extract main product category/type from idea text
        product_type = self._extract_product_type(idea_text, keywords)
        
        # Generate search queries
        queries = []
        
        # Add basic keyword searches - avoid redundancy like "software software"
        for keyword in keywords[:3]:  # Use top 3 keywords
            # Check if keyword already contains "software" or "tool"
            if "software" not in keyword.lower():
                queries.append(f"{keyword} software")
            if "tool" not in keyword.lower():
                queries.append(f"{keyword} tool")
            # Add the keyword by itself for broader results
            queries.append(keyword)
        
        # Add competitor-focused queries
        if product_type:
            queries.append(f"best {product_type} software")
            queries.append(f"top {product_type} tools")
            queries.append(f"{product_type} software alternatives")
            queries.append(f"{product_type} competitors")
            queries.append(f"{product_type} companies")
        
        # Add specific competitor research queries
        for keyword in keywords[:2]:  # Use top 2 keywords
            if "software" not in keyword.lower():
                queries.append(f"alternatives to {keyword} software")
                queries.append(f"{keyword} software competitors")
            else:
                queries.append(f"alternatives to {keyword}")
                queries.append(f"{keyword} competitors")
            
        # Add market trend queries
        queries.append(f"{' '.join(keywords[:2])} market trends")
        queries.append(f"{' '.join(keywords[:2])} industry statistics")
        
        # Remove duplicates and return
        return list(dict.fromkeys(queries))
    
    def _extract_product_type(self, idea_text: str, keywords: List[str]) -> Optional[str]:
        """
        Extract the main product type/category from the idea text.
        
        Args:
            idea_text: Original idea text
            keywords: Extracted keywords
            
        Returns:
            Product type string or None if not found
        """
        # Common SaaS product type patterns
        patterns = [
            r'([\w\s]+) (software|platform|tool|solution|app|application)',
            r'([\w\s]+) for ([\w\s]+)',
            r'([\w\s]+) to (manage|track|monitor|analyze|automate) ([\w\s]+)'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, idea_text, re.IGNORECASE)
            if matches:
                if isinstance(matches[0], tuple):
                    # Return the most relevant part of the match
                    return matches[0][0].strip().lower()
                return matches[0].strip().lower()
        
        # Fallback to first keyword if no pattern matches
        return keywords[0] if keywords else None
    
    async def _execute_search(self, query: str) -> Dict[str, Any]:
        """
        Execute a Google search query and parse the results.
        
        Args:
            query: Search query string
            
        Returns:
            Dictionary containing parsed search results
        """
        # Encode query for URL
        encoded_query = quote_plus(query)
        
        # Construct search URL
        url = f"{self.base_url}?q={encoded_query}&num={self.num_results}"
        
        # Select random user agent
        headers = {
            "User-Agent": random.choice(self.user_agents),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Referer": "https://www.google.com/",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1"
        }
        
        # Setup proxy if configured
        proxy = self.proxy
        
        # Execute request with retries
        for attempt in range(self.max_retries):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        url,
                        headers=headers,
                        proxy=proxy,
                        timeout=aiohttp.ClientTimeout(total=self.timeout)
                    ) as response:
                        if response.status == 200:
                            html_content = await response.text()
                            return self._parse_search_results(html_content, query)
                        elif response.status == 429:  # Too Many Requests
                            logger.warning(f"Rate limited by Google (429). Attempt {attempt + 1}/{self.max_retries}")
                            # Exponential backoff
                            await asyncio.sleep(2 ** attempt + random.random())
                            continue
                        else:
                            logger.warning(f"Google search failed with status {response.status}. Attempt {attempt + 1}/{self.max_retries}")
                            # Try with a different user agent
                            headers["User-Agent"] = random.choice(self.user_agents)
                            await asyncio.sleep(1)
                            continue
            except asyncio.TimeoutError:
                logger.warning(f"Google search timed out. Attempt {attempt + 1}/{self.max_retries}")
                await asyncio.sleep(1)
                continue
            except Exception as e:
                logger.warning(f"Google search request failed: {str(e)}. Attempt {attempt + 1}/{self.max_retries}")
                await asyncio.sleep(1)
                continue
        
        # If all retries failed, raise exception
        raise Exception(f"Failed to execute Google search for query '{query}' after {self.max_retries} attempts")
    
    def _parse_search_results(self, html_content: str, query: str) -> Dict[str, Any]:
        """
        Parse Google search results HTML.
        
        Args:
            html_content: HTML content from Google search
            query: Original search query
            
        Returns:
            Dictionary containing parsed search results
        """
        results = {
            "query": query,
            "organic_results": [],
            "featured_snippet": None,
            "knowledge_panel": None,
            "related_searches": []
        }
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Save the HTML for debugging
            debug_file = f"google_debug_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
            with open(debug_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
            logger.info(f"Saved debug HTML to {debug_file}")
            
            # Extract organic search results - try multiple selectors to handle Google's changing structure
            result_selectors = [
                'div.g', 
                'div.tF2Cxc', 
                'div.yuRUbf',
                'div[data-sokoban-container]',
                'div.rc',
                'div.jtfYYd',
                'div.mnr-c',
                # Additional selectors for modern Google results
                'div.MjjYud',
                'div.v7W49e',
                'div.hlcw0c',
                'div.g.Ww4FFb.vt6azd.tF2Cxc',
                'div.kvH3mc.BToiNc.UK95Uc',
                'div.Z26q7c.UK95Uc.jGGQ5e',
                'div.g div.BYM4Nd',
                'div.g div.tF2Cxc',
                'div.g div.kvH3mc'
            ]
            
            # Try each selector until we find results
            for selector in result_selectors:
                results_found = False
                for result in soup.select(selector):
                    try:
                        # Try multiple title selectors
                        title_element = (
                            result.select_one('h3') or 
                            result.select_one('h3.LC20lb') or
                            result.select_one('.DKV0Md') or
                            result.select_one('[role="heading"]') or
                            result.select_one('a h3') or
                            result.select_one('h3.zBAuLc') or
                            result.select_one('h3.DFN0Dc')
                        )
                        
                        # Try multiple link selectors
                        link_element = (
                            result.select_one('a[href]') or
                            result.select_one('a.cz3goc') or
                            result.select_one('div.yuRUbf a') or
                            result.select_one('div.Z26q7c a') or
                            result.select_one('div.kvH3mc a')
                        )
                        
                        # Try multiple snippet selectors
                        snippet_element = (
                            result.select_one('div.VwiC3b') or
                            result.select_one('span.aCOpRe') or
                            result.select_one('div.s3v9rd') or
                            result.select_one('div.lEBKkf') or
                            result.select_one('div.yXK7lf') or
                            result.select_one('div.Z26q7c div.VwiC3b') or
                            result.select_one('div.kvH3mc div.VwiC3b') or
                            result.select_one('div.HiHjCd') or
                            result.select_one('div.BNeawe.s3v9rd.AP7Wnd')
                        )
                        
                        if title_element and link_element and 'href' in link_element.attrs:
                            title = title_element.get_text()
                            link = link_element['href']
                            snippet = snippet_element.get_text() if snippet_element else ""
                            
                            # Skip Google-specific links
                            if link.startswith('/'):
                                continue
                                
                            # Skip if link contains google.com
                            if 'google.com' in link:
                                continue
                                
                            results["organic_results"].append({
                                "title": title,
                                "link": link,
                                "snippet": snippet
                            })
                            results_found = True
                            
                            # Log successful extraction
                            logger.debug(f"Extracted result: {title} - {link}")
                    except Exception as e:
                        logger.debug(f"Failed to parse search result: {str(e)}")
                        continue
                
                # If we found results with this selector, stop trying others
                if results_found:
                    logger.info(f"Found {len(results['organic_results'])} results with selector: {selector}")
                    break
            
            # If we still don't have results, try a more generic approach
            if not results["organic_results"]:
                logger.info("No results found with specific selectors, trying generic approach")
                # Look for any heading followed by a link
                headings = soup.find_all(['h3', 'h2'])
                for heading in headings:
                    try:
                        # Find closest link
                        link_element = heading.find_parent('a') or heading.find_next('a')
                        if link_element and 'href' in link_element.attrs:
                            link = link_element['href']
                            if not link.startswith('/') and 'google.com' not in link:
                                # Find snippet - any div or span near the heading
                                snippet_element = heading.find_next(['div', 'span'])
                                snippet = snippet_element.get_text() if snippet_element else ""
                                
                                results["organic_results"].append({
                                    "title": heading.get_text(),
                                    "link": link,
                                    "snippet": snippet
                                })
                                logger.debug(f"Extracted result with generic approach: {heading.get_text()} - {link}")
                    except Exception as e:
                        continue
            
            # Extract featured snippet if present - try multiple selectors
            featured_selectors = ['div.c2xzTb', 'div.IZ6rdc', 'div.xpdopen', 'div.kp-wholepage', 'div.ifM9O']
            for selector in featured_selectors:
                featured_snippet = soup.select_one(selector)
                if featured_snippet:
                    snippet_text = featured_snippet.get_text()
                    results["featured_snippet"] = snippet_text
                    logger.debug(f"Extracted featured snippet with selector: {selector}")
                    break
            
            # Extract related searches - try multiple selectors
            related_selectors = [
                'div.AJLUJb > div > a', 
                'div.brs_col a', 
                'div.s75CSd',
                'div.card-section a'
            ]
            for selector in related_selectors:
                related_searches = soup.select(selector)
                if related_searches:
                    for related in related_searches:
                        results["related_searches"].append(related.get_text())
                    logger.debug(f"Extracted {len(results['related_searches'])} related searches with selector: {selector}")
                    break
            
            # Save the HTML for debugging if no results were found
            if not results["organic_results"]:
                logger.warning(f"No results found for query: {query}")
                # Try a last-resort approach - find all links with text
                all_links = soup.find_all('a')
                for link in all_links:
                    if link.get_text() and 'href' in link.attrs:
                        href = link['href']
                        if href.startswith('http') and 'google.com' not in href:
                            results["organic_results"].append({
                                "title": link.get_text().strip(),
                                "link": href,
                                "snippet": ""
                            })
                            logger.debug(f"Last resort extraction: {link.get_text().strip()} - {href}")
            
            logger.info(f"Extracted {len(results['organic_results'])} organic results for query: {query}")
            return results
            
        except Exception as e:
            logger.warning(f"Failed to parse Google search results: {str(e)}")
            return results
    
    def _extract_competitors(self, search_results: Dict[str, Any], query: str) -> List[CompetitorData]:
        """
        Extract competitor information from search results.
        
        Args:
            search_results: Parsed search results
            query: Original search query
            
        Returns:
            List of CompetitorData objects
        """
        competitors = []
        
        # Process organic results
        for result in search_results.get("organic_results", []):
            title = result.get("title", "")
            snippet = result.get("snippet", "")
            link = result.get("link", "")
            
            # Skip if no title or link
            if not title or not link:
                continue
                
            # Check if result appears to be a competitor
            if self._is_likely_competitor(title, snippet, query):
                # Extract company/product name
                company_name = self._extract_company_name(title, link)
                
                if company_name:
                    # Estimate users based on domain authority and position
                    estimated_users = self._estimate_users(link, title)
                    
                    # Estimate revenue based on estimated users
                    estimated_revenue = self._estimate_revenue(estimated_users)
                    
                    # Create competitor data
                    competitor = CompetitorData(
                        name=company_name,
                        description=snippet[:200] if snippet else "",
                        website=link,
                        source=self.source_name,
                        source_url=link,
                        confidence_score=self._calculate_competitor_confidence(title, snippet, query),
                        estimated_users=estimated_users,
                        estimated_revenue=estimated_revenue,
                        pricing_model=self._extract_pricing_model(snippet)
                    )
                    
                    # Try to extract additional information
                    self._enrich_competitor_data(competitor, title, snippet)
                    
                    competitors.append(competitor)
        
        return competitors
        
    def _estimate_users(self, website: str, title: str) -> Optional[int]:
        """
        Estimate user count based on domain and title keywords.
        
        Args:
            website: Website URL
            title: Result title
            
        Returns:
            Estimated user count or None
        """
        # Base estimate on domain authority indicators
        base_estimate = 1000  # Default base estimate
        
        # Check for well-known domains
        domain = urlparse(website).netloc.lower()
        
        # Major players get higher estimates
        if any(big_domain in domain for big_domain in ['salesforce', 'hubspot', 'zoho', 'microsoft']):
            return random.randint(500000, 2000000)
        
        # Medium-sized players
        if any(mid_domain in domain for mid_domain in ['pipedrive', 'freshworks', 'zendesk', 'monday']):
            return random.randint(100000, 500000)
        
        # Adjust based on title keywords
        title_lower = title.lower()
        
        # Look for indicators of popularity
        if any(indicator in title_lower for indicator in ['leading', 'top', 'best', '#1']):
            base_estimate *= 5
        
        # Look for scale indicators
        if any(indicator in title_lower for indicator in ['enterprise', 'global']):
            base_estimate *= 3
        elif any(indicator in title_lower for indicator in ['small business', 'startup']):
            base_estimate *= 0.5
            
        # Add some randomness
        return int(base_estimate * random.uniform(0.8, 1.2))
        
    def _estimate_revenue(self, estimated_users: Optional[int]) -> Optional[str]:
        """
        Estimate revenue based on user count.
        
        Args:
            estimated_users: Estimated user count
            
        Returns:
            Revenue estimate string or None
        """
        if not estimated_users:
            return None
            
        if estimated_users > 500000:
            return "$100M+ ARR"
        elif estimated_users > 100000:
            return "$50M+ ARR"
        elif estimated_users > 50000:
            return "$10M+ ARR"
        elif estimated_users > 10000:
            return "$1M+ ARR"
        elif estimated_users > 5000:
            return "$500K+ ARR"
        elif estimated_users > 1000:
            return "$100K+ ARR"
        else:
            return "Early stage"
            
    def _enrich_competitor_data(self, competitor: CompetitorData, title: str, snippet: str) -> None:
        """
        Enrich competitor data with additional information.
        
        Args:
            competitor: CompetitorData object to enrich
            title: Result title
            snippet: Result snippet
        """
        combined_text = f"{title} {snippet}".lower()
        
        # Try to extract launch date
        date_patterns = [
            r'founded in (\d{4})',
            r'since (\d{4})',
            r'established in (\d{4})'
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, combined_text)
            if match:
                competitor.launch_date = match.group(1)
                break
                
        # Try to extract founder/CEO
        founder_patterns = [
            r'founded by ([A-Z][a-z]+ [A-Z][a-z]+)',
            r'CEO ([A-Z][a-z]+ [A-Z][a-z]+)'
        ]
        
        for pattern in founder_patterns:
            match = re.search(pattern, combined_text)
            if match:
                competitor.founder_ceo = match.group(1)
                break
                
        # Try to extract ratings
        rating_patterns = [
            r'(\d+\.?\d*)/5',
            r'(\d+\.?\d*) out of 5',
            r'(\d+\.?\d*) stars'
        ]
        
        for pattern in rating_patterns:
            match = re.search(pattern, combined_text)
            if match:
                try:
                    competitor.average_rating = float(match.group(1))
                    break
                except:
                    pass
                    
        # Try to extract review count
        review_patterns = [
            r'(\d+,?\d*) reviews',
            r'(\d+,?\d*) ratings'
        ]
        
        for pattern in review_patterns:
            match = re.search(pattern, combined_text)
            if match:
                try:
                    review_count = match.group(1).replace(',', '')
                    competitor.review_count = int(review_count)
                    break
                except:
                    pass
    
    def _is_likely_competitor(self, title: str, snippet: str, query: str) -> bool:
        """
        Determine if a search result is likely to be a competitor.
        
        Args:
            title: Result title
            snippet: Result snippet
            query: Original search query
            
        Returns:
            True if likely a competitor, False otherwise
        """
        # For debugging
        logger.debug(f"Checking if result is competitor: {title}")
        
        # If title or snippet is empty, it's not a competitor
        if not title or not snippet:
            return False
            
        combined_text = f"{title.lower()} {snippet.lower()}"
        query_lower = query.lower()
        
        # Check for competitor indicators
        competitor_indicators = [
            "software", "platform", "tool", "solution", "app", "saas",
            "service", "product", "suite", "system", "crm", "customer relationship",
            "management", "business", "enterprise", "cloud", "api", "dashboard",
            "analytics", "automation", "integration", "workflow", "pipeline"
        ]
        
        # Check for non-competitor indicators
        non_competitor_indicators = [
            "wikipedia", "definition", "what is", "how to", "tutorial",
            "guide", "blog", "news", "article", "forum", "reddit", "quora",
            "stack overflow", "github", "youtube", "facebook", "twitter",
            "instagram", "linkedin", "pinterest", "tiktok", "dictionary"
        ]
        
        # Check if title contains competitor indicators
        has_competitor_indicator = any(indicator in combined_text for indicator in competitor_indicators)
        
        # Check if title contains non-competitor indicators
        has_non_competitor_indicator = any(indicator in combined_text for indicator in non_competitor_indicators)
        
        # Check if query is competitor-focused
        is_competitor_query = any(pattern in query_lower for pattern in [
            "alternative", "competitor", "vs", "versus", "comparison", "best", "top"
        ])
        
        # Check for company/product name patterns
        has_product_pattern = bool(re.search(r'[A-Z][a-z]+(?:CRM|HQ|App|\.io|\.com|\.ai)', title))
        
        # Check for pricing mentions which often indicate products
        has_pricing_mention = any(term in combined_text for term in [
            "pricing", "subscription", "monthly", "annually", "free trial",
            "premium", "basic plan", "enterprise plan", "per user", "per month"
        ])
        
        # If the query explicitly mentions a product category, be more lenient
        product_category_mentioned = any(category in query_lower for category in [
            "crm", "software", "tool", "platform", "solution", "app"
        ])
        
        # Check for company name patterns (capitalized words)
        has_company_name = bool(re.search(r'\b[A-Z][a-z]+\b', title))
        
        # Check for domain name in title
        has_domain = bool(re.search(r'\b[a-zA-Z0-9]+\.[a-z]{2,}\b', title))
        
        # For CRM-specific queries, be more lenient
        is_crm_query = "crm" in query_lower
        
        # Combine all signals
        is_competitor = (
            (has_competitor_indicator and not has_non_competitor_indicator) or
            is_competitor_query or
            has_product_pattern or
            has_pricing_mention or
            (product_category_mentioned and not has_non_competitor_indicator) or
            (has_company_name and has_competitor_indicator) or
            (has_domain and has_competitor_indicator) or
            (is_crm_query and has_company_name)
        )
        
        # Log the decision
        if is_competitor:
            logger.debug(f"Identified as competitor: {title}")
        
        return is_competitor
    
    def _extract_company_name(self, title: str, url: str) -> Optional[str]:
        """
        Extract company or product name from title and URL.
        
        Args:
            title: Result title
            url: Result URL
            
        Returns:
            Company/product name or None if not found
        """
        # Try to extract from title first - expanded patterns
        title_patterns = [
            r'^([A-Z][a-zA-Z0-9]+(?:\s[A-Z][a-zA-Z0-9]+)?)(?:\s*[-|:]\s*.+)?$',  # "ProductName - description" or "Product Name - description"
            r'^([A-Z][a-zA-Z0-9]+(?:\s[A-Z][a-zA-Z0-9]+)?)(?:\s*\|\s*.+)?$',     # "ProductName | description" or "Product Name | description"
            r'^([A-Z][a-zA-Z0-9]+(?:\.\w+)?)(?:\s*[-|:]\s*.+)?$',                # "Product.io - description"
            r'^([A-Z][a-zA-Z0-9]+(?:CRM|HQ|App|\.io|\.com|\.ai))(?:\s*.+)?$',    # "ProductCRM" or "Product.io"
            r'^([A-Z][a-zA-Z0-9]+\s(?:CRM|Software|Platform|Tool|App))(?:\s*.+)?$', # "Product CRM" or "Product Software"
        ]
        
        for pattern in title_patterns:
            match = re.match(pattern, title)
            if match:
                return match.group(1).strip()
        
        # Try to extract from domain
        try:
            domain = urlparse(url).netloc
            
            # Remove www. and common TLDs
            domain = re.sub(r'^www\.', '', domain)
            domain = re.sub(r'\.(com|org|net|io|co|app|ai)$', '', domain)
            
            # Handle subdomains
            domain_parts = domain.split('.')
            if len(domain_parts) > 1:
                # Use the most significant part (usually the second-to-last)
                domain = domain_parts[-2]
            else:
                domain = domain_parts[0]
            
            # Convert to title case for better readability
            if domain and len(domain) >= 2:
                # Handle special cases like "salesforce" -> "Salesforce"
                if domain.lower() in ["salesforce", "hubspot", "zoho", "pipedrive", "freshworks"]:
                    return domain.title()
                # Handle camelCase or kebab-case domains
                if '-' in domain:
                    parts = domain.split('-')
                    return ' '.join(part.title() for part in parts)
                # Add space before capital letters in camelCase
                domain_with_spaces = re.sub(r'([a-z])([A-Z])', r'\1 \2', domain)
                return domain_with_spaces.title()
        except:
            pass
        
        # Try to find a product name pattern in the title
        product_pattern = re.search(r'([A-Z][a-zA-Z0-9]+(?:CRM|HQ|App|\.io|\.com|\.ai))', title)
        if product_pattern:
            return product_pattern.group(1)
        
        # If all else fails, use the first 2-3 words of the title
        words = title.split()
        if words:
            # Skip common prefixes like "Best" or "Top"
            if words[0].lower() in ["best", "top", "leading", "popular", "free", "affordable"]:
                words = words[1:]
            return ' '.join(words[:min(3, len(words))])
        
        return None
    
    def _calculate_competitor_confidence(self, title: str, snippet: str, query: str) -> float:
        """
        Calculate confidence score for competitor identification.
        
        Args:
            title: Result title
            snippet: Result snippet
            query: Original search query
            
        Returns:
            Confidence score between 0.0 and 1.0
        """
        combined_text = f"{title.lower()} {snippet.lower()}"
        base_score = 0.5
        
        # Adjust based on competitor indicators in text
        strong_indicators = [
            "alternative to", "competitor to", "similar to",
            "vs", "versus", "comparison", "pricing", "features"
        ]
        
        # Check for strong indicators
        for indicator in strong_indicators:
            if indicator in combined_text:
                base_score += 0.1
        
        # Adjust based on query type
        if "alternative" in query.lower() or "competitor" in query.lower():
            base_score += 0.2
        elif "best" in query.lower() or "top" in query.lower():
            base_score += 0.15
        
        # Cap at 0.95 to account for uncertainty
        return min(0.95, base_score)
    
    def _extract_pricing_model(self, snippet: str) -> Optional[str]:
        """
        Extract pricing model information from snippet.
        
        Args:
            snippet: Result snippet
            
        Returns:
            Pricing model string or None if not found
        """
        snippet_lower = snippet.lower()
        
        # Check for pricing indicators
        if "free" in snippet_lower and ("premium" in snippet_lower or "paid" in snippet_lower):
            return "Freemium"
        elif "subscription" in snippet_lower:
            return "Subscription"
        elif "one-time" in snippet_lower or "one time" in snippet_lower:
            return "One-time purchase"
        elif "free" in snippet_lower:
            return "Free"
        elif "trial" in snippet_lower:
            return "Free trial"
        
        return None
    
    def _extract_feedback(self, search_results: Dict[str, Any], query: str) -> List[FeedbackData]:
        """
        Extract market feedback from search results.
        
        Args:
            search_results: Parsed search results
            query: Original search query
            
        Returns:
            List of FeedbackData objects
        """
        feedback = []
        
        # Extract feedback from featured snippet
        featured_snippet = search_results.get("featured_snippet")
        if featured_snippet:
            sentiment, sentiment_score = self._analyze_sentiment(featured_snippet)
            
            feedback_data = FeedbackData(
                text=featured_snippet[:500],  # Limit text length
                sentiment=sentiment,
                sentiment_score=sentiment_score,
                source=self.source_name,
                source_url=f"https://www.google.com/search?q={quote_plus(query)}",
                author_info={
                    "type": "featured_snippet",
                    "query": query
                }
            )
            
            feedback.append(feedback_data)
        
        # Extract feedback from organic results that contain reviews or opinions
        for result in search_results.get("organic_results", []):
            title = result.get("title", "")
            snippet = result.get("snippet", "")
            link = result.get("link", "")
            
            # Skip if no snippet
            if not snippet:
                continue
                
            # Check if snippet contains feedback indicators
            if self._contains_feedback_indicators(title, snippet):
                sentiment, sentiment_score = self._analyze_sentiment(snippet)
                
                feedback_data = FeedbackData(
                    text=snippet[:500],  # Limit text length
                    sentiment=sentiment,
                    sentiment_score=sentiment_score,
                    source=self.source_name,
                    source_url=link,
                    author_info={
                        "type": "search_result",
                        "title": title,
                        "query": query
                    }
                )
                
                feedback.append(feedback_data)
        
        return feedback
    
    def _contains_feedback_indicators(self, title: str, snippet: str) -> bool:
        """
        Check if text contains feedback indicators.
        
        Args:
            title: Result title
            snippet: Result snippet
            
        Returns:
            True if contains feedback indicators, False otherwise
        """
        combined_text = f"{title.lower()} {snippet.lower()}"
        
        feedback_indicators = [
            "review", "opinion", "experience", "testimonial",
            "rating", "star", "recommend", "feedback", "thought",
            "pros and cons", "advantage", "disadvantage",
            "like", "dislike", "love", "hate"
        ]
        
        return any(indicator in combined_text for indicator in feedback_indicators)
    
    def _analyze_sentiment(self, text: str) -> tuple[str, float]:
        """
        Basic sentiment analysis using keyword matching.
        
        Args:
            text: Text to analyze
            
        Returns:
            Tuple of (sentiment, sentiment_score)
        """
        text_lower = text.lower()
        
        # Positive indicators
        positive_words = [
            'great', 'awesome', 'excellent', 'amazing', 'fantastic', 'wonderful',
            'love', 'like', 'good', 'best', 'perfect', 'helpful', 'useful',
            'recommend', 'impressed', 'satisfied', 'happy', 'pleased'
        ]
        
        # Negative indicators
        negative_words = [
            'bad', 'terrible', 'awful', 'horrible', 'hate', 'dislike', 'worst',
            'useless', 'broken', 'frustrated', 'disappointed', 'annoying',
            'problem', 'issue', 'bug', 'error', 'fail', 'sucks', 'waste'
        ]
        
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        if positive_count > negative_count:
            sentiment = "positive"
            sentiment_score = min(0.8, 0.3 + (positive_count * 0.1))
        elif negative_count > positive_count:
            sentiment = "negative"
            sentiment_score = max(-0.8, -0.3 - (negative_count * 0.1))
        else:
            sentiment = "neutral"
            sentiment_score = 0.0
        
        return sentiment, sentiment_score
    
    def _deduplicate_competitors(self, competitors: List[CompetitorData]) -> List[CompetitorData]:
        """
        Remove duplicate competitors based on name.
        
        Args:
            competitors: List of CompetitorData objects
            
        Returns:
            List of unique CompetitorData objects
        """
        unique_competitors = {}
        
        for competitor in competitors:
            name_lower = competitor.name.lower()
            
            if name_lower not in unique_competitors:
                unique_competitors[name_lower] = competitor
            else:
                # If duplicate, keep the one with higher confidence score
                if competitor.confidence_score > unique_competitors[name_lower].confidence_score:
                    unique_competitors[name_lower] = competitor
        
        return list(unique_competitors.values())
    
    def _deduplicate_feedback(self, feedback: List[FeedbackData]) -> List[FeedbackData]:
        """
        Remove duplicate feedback based on text similarity.
        
        Args:
            feedback: List of FeedbackData objects
            
        Returns:
            List of unique FeedbackData objects
        """
        unique_feedback = []
        seen_texts = set()
        
        for item in feedback:
            # Create a normalized version for comparison
            normalized_text = re.sub(r'\s+', ' ', item.text.lower().strip())
            
            # Skip if we've seen very similar text
            if normalized_text not in seen_texts:
                seen_texts.add(normalized_text)
                unique_feedback.append(item)
        
        return unique_feedback