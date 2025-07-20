"""
Scraping service to orchestrate parallel scraping from multiple sources.
"""
import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from ..scrapers.base_scraper import BaseScraper, ScrapingResult, ScrapingStatus, CompetitorData, FeedbackData
from ..utils.keyword_extractor import KeywordExtractor
from ..utils.data_cleaner import DataCleaner


logger = logging.getLogger(__name__)


class ScrapingService:
    """Service to orchestrate parallel scraping from multiple sources."""
    
    def __init__(self):
        """Initialize the scraping service."""
        self.scrapers: List[BaseScraper] = []
        self.max_concurrent_scrapers = 6
        self.total_timeout = 300  # 5 minutes total timeout
    
    def register_scraper(self, scraper: BaseScraper) -> None:
        """
        Register a scraper with the service.
        
        Args:
            scraper: The scraper instance to register
        """
        if scraper.validate_config():
            self.scrapers.append(scraper)
            logger.info(f"Registered scraper: {scraper.get_source_name()}")
        else:
            logger.warning(f"Scraper {scraper.get_source_name()} failed validation")
    
    def get_registered_scrapers(self) -> List[str]:
        """Get list of registered scraper names."""
        return [scraper.get_source_name() for scraper in self.scrapers]
    
    async def scrape_all_sources(self, idea_text: str, validation_id: str) -> Dict[str, Any]:
        """
        Scrape all registered sources in parallel.
        
        Args:
            idea_text: The business idea text to analyze
            validation_id: Unique identifier for this validation
            
        Returns:
            Dictionary containing aggregated results and metadata
        """
        if not self.scrapers:
            logger.warning("No scrapers registered")
            return self._create_empty_result()
        
        # Extract keywords from idea text
        keywords = KeywordExtractor.extract_keywords(idea_text)
        logger.info(f"Extracted keywords: {keywords}")
        
        # Start scraping all sources in parallel
        start_time = datetime.utcnow()
        
        try:
            # Create semaphore to limit concurrent scrapers
            semaphore = asyncio.Semaphore(self.max_concurrent_scrapers)
            
            # Create scraping tasks
            tasks = []
            for scraper in self.scrapers:
                task = self._scrape_with_semaphore(semaphore, scraper, keywords, idea_text)
                tasks.append(task)
            
            # Wait for all tasks to complete with timeout
            results = await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=True),
                timeout=self.total_timeout
            )
            
            # Process results
            return self._process_scraping_results(results, start_time, validation_id)
            
        except asyncio.TimeoutError:
            logger.error(f"Scraping timeout after {self.total_timeout} seconds")
            return self._create_timeout_result(start_time)
        except Exception as e:
            logger.error(f"Unexpected error during scraping: {str(e)}")
            return self._create_error_result(str(e), start_time)
    
    async def _scrape_with_semaphore(
        self, 
        semaphore: asyncio.Semaphore, 
        scraper: BaseScraper, 
        keywords: List[str], 
        idea_text: str
    ) -> tuple:
        """
        Scrape with semaphore to limit concurrency.
        
        Returns:
            Tuple of (scraper_name, result_or_exception)
        """
        async with semaphore:
            try:
                logger.info(f"Starting scraping for {scraper.get_source_name()}")
                result = await scraper.scrape(keywords, idea_text)
                logger.info(f"Completed scraping for {scraper.get_source_name()}: {result.status}")
                return (scraper.get_source_name(), result)
            except Exception as e:
                logger.error(f"Error scraping {scraper.get_source_name()}: {str(e)}")
                return (scraper.get_source_name(), e)
    
    def _process_scraping_results(
        self, 
        results: List[Any], 
        start_time: datetime, 
        validation_id: str
    ) -> Dict[str, Any]:
        """Process the results from all scrapers."""
        all_competitors = []
        all_feedback = []
        successful_sources = []
        failed_sources = []
        partial_sources = []
        
        for result in results:
            if isinstance(result, tuple):
                source_name, scraping_result = result
                
                if isinstance(scraping_result, Exception):
                    # Handle exception
                    failed_sources.append({
                        'source': source_name,
                        'error': str(scraping_result)
                    })
                elif isinstance(scraping_result, ScrapingResult):
                    # Handle successful result
                    if scraping_result.status == ScrapingStatus.SUCCESS:
                        successful_sources.append(source_name)
                    elif scraping_result.status == ScrapingStatus.PARTIAL_SUCCESS:
                        partial_sources.append({
                            'source': source_name,
                            'message': scraping_result.error_message
                        })
                    else:
                        failed_sources.append({
                            'source': source_name,
                            'error': scraping_result.error_message
                        })
                    
                    # Collect data regardless of status
                    all_competitors.extend(scraping_result.competitors or [])
                    all_feedback.extend(scraping_result.feedback or [])
        
        # Clean and deduplicate data
        cleaned_competitors = DataCleaner.clean_competitors(all_competitors)
        cleaned_feedback = DataCleaner.clean_feedback(all_feedback)
        
        # Calculate processing time
        end_time = datetime.utcnow()
        processing_time = (end_time - start_time).total_seconds()
        
        return {
            'competitors': cleaned_competitors,
            'feedback': cleaned_feedback,
            'metadata': {
                'validation_id': validation_id,
                'processing_time_seconds': processing_time,
                'sources_attempted': len(self.scrapers),
                'sources_successful': len(successful_sources),
                'sources_partial': len(partial_sources),
                'sources_failed': len(failed_sources),
                'successful_sources': successful_sources,
                'partial_sources': partial_sources,
                'failed_sources': failed_sources,
                'total_competitors_found': len(cleaned_competitors),
                'total_feedback_found': len(cleaned_feedback),
                'completed_at': end_time.isoformat()
            }
        }
    
    def _create_empty_result(self) -> Dict[str, Any]:
        """Create empty result when no scrapers are registered."""
        return {
            'competitors': [],
            'feedback': [],
            'metadata': {
                'processing_time_seconds': 0,
                'sources_attempted': 0,
                'sources_successful': 0,
                'sources_partial': 0,
                'sources_failed': 0,
                'successful_sources': [],
                'partial_sources': [],
                'failed_sources': [],
                'total_competitors_found': 0,
                'total_feedback_found': 0,
                'error': 'No scrapers registered'
            }
        }
    
    def _create_timeout_result(self, start_time: datetime) -> Dict[str, Any]:
        """Create result for timeout scenario."""
        end_time = datetime.utcnow()
        processing_time = (end_time - start_time).total_seconds()
        
        return {
            'competitors': [],
            'feedback': [],
            'metadata': {
                'processing_time_seconds': processing_time,
                'sources_attempted': len(self.scrapers),
                'sources_successful': 0,
                'sources_partial': 0,
                'sources_failed': len(self.scrapers),
                'successful_sources': [],
                'partial_sources': [],
                'failed_sources': [{'source': s.get_source_name(), 'error': 'Timeout'} for s in self.scrapers],
                'total_competitors_found': 0,
                'total_feedback_found': 0,
                'error': f'Scraping timeout after {self.total_timeout} seconds'
            }
        }
    
    def _create_error_result(self, error_message: str, start_time: datetime) -> Dict[str, Any]:
        """Create result for unexpected error scenario."""
        end_time = datetime.utcnow()
        processing_time = (end_time - start_time).total_seconds()
        
        return {
            'competitors': [],
            'feedback': [],
            'metadata': {
                'processing_time_seconds': processing_time,
                'sources_attempted': len(self.scrapers),
                'sources_successful': 0,
                'sources_partial': 0,
                'sources_failed': len(self.scrapers),
                'successful_sources': [],
                'partial_sources': [],
                'failed_sources': [{'source': s.get_source_name(), 'error': error_message} for s in self.scrapers],
                'total_competitors_found': 0,
                'total_feedback_found': 0,
                'error': error_message
            }
        }