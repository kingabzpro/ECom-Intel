import os
import re
import json
from typing import List, Dict, Optional
from urllib.parse import urljoin, urlparse
import requests
from dotenv import load_dotenv

load_dotenv()

class FirecrawlClient:
    def __init__(self):
        self.api_key = os.getenv('FIRECRAWL_API_KEY')
        if not self.api_key:
            raise ValueError("FIRECRAWL_API_KEY not found in environment variables")

        self.base_url = "https://api.firecrawl.dev/v1"
        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }

    def search_reviews(self, product_url: str, max_results: int = 10) -> List[str]:
        """Search for review pages related to the product."""
        try:
            # Extract product name/brand from URL for better search
            product_info = self._extract_product_info(product_url)

            # Construct search queries
            search_queries = [
                f"{product_info.get('name', '')} reviews",
                f"{product_info.get('brand', '')} {product_info.get('name', '')} customer reviews",
                f"{product_info.get('name', '')} user feedback rating"
            ]

            review_urls = []

            for query in search_queries:
                try:
                    # Use Firecrawl search API
                    search_url = f"{self.base_url}/search"
                    payload = {
                        "query": query,
                        "limit": max_results,
                        "scrapeOptions": {
                            "formats": ["markdown"],
                            "onlyMainContent": True
                        }
                    }

                    response = requests.post(search_url, headers=self.headers, json=payload)

                    if response.status_code == 200:
                        results = response.json()
                        if 'data' in results and results['data']:
                            for item in results['data']:
                                if 'url' in item:
                                    review_urls.append(item['url'])
                except Exception as e:
                    print(f"Search error for query '{query}': {str(e)}")
                    continue

            # Remove duplicates and return
            return list(set(review_urls))

        except Exception as e:
            print(f"Error searching for reviews: {str(e)}")
            return []

    def scrape_reviews(self, url: str) -> Dict:
        """Scrape review content from a URL."""
        try:
            scrape_url = f"{self.base_url}/scrape"
            payload = {
                "url": url,
                "formats": ["markdown"],
                "onlyMainContent": True,
                "waitFor": 2000,  # Wait 2 seconds for dynamic content
                "includeTags": ["div", "span", "p", "article", "section"],
                "excludeTags": ["script", "style", "nav", "footer", "header"]
            }

            response = requests.post(scrape_url, headers=self.headers, json=payload)

            if response.status_code == 200:
                result = response.json()
                if 'data' in result:
                    return {
                        'url': url,
                        'content': result['data'].get('markdown', ''),
                        'success': True
                    }

            return {'url': url, 'content': '', 'success': False, 'error': f"HTTP {response.status_code}"}

        except Exception as e:
            return {'url': url, 'content': '', 'success': False, 'error': str(e)}

    def extract_reviews_from_content(self, content: str, source_url: str) -> List[Dict]:
        """Extract individual reviews from scraped content."""
        reviews = []

        # Common review patterns
        review_patterns = [
            r'(\d+(?:\.\d+)?)\s*stars?\s*(.*?)(?=\d+(?:\.\d+)?\s*stars?|$)',
            r'Rating[:\s]*(\d+(?:\.\d+)?)[\s\S]*?(.*?)(?=Rating[:\s]*\d+(?:\.\d+)?|$)',
            r'(\d+)\/5\s*(.*?)(?=\d+\/5|$)',
            r'★{1,5}\s*(.*?)(?=★{1,5}|$)'
        ]

        # Split content into potential review sections
        lines = content.split('\n')
        current_review = ""
        current_rating = None

        for i, line in enumerate(lines):
            line = line.strip()
            if not line or len(line) < 10:
                continue

            # Look for ratings
            rating_match = None
            for pattern in review_patterns:
                match = re.search(pattern, line, re.IGNORECASE)
                if match:
                    rating_match = match
                    break

            if rating_match:
                # Save previous review if exists
                if current_review and current_rating:
                    reviews.append({
                        'review_text': current_review.strip(),
                        'rating': self._normalize_rating(current_rating),
                        'reviewer_name': self._extract_reviewer_name(current_review),
                        'review_date': self._extract_review_date(current_review),
                        'source_url': source_url
                    })

                # Start new review
                current_rating = rating_match.group(1)
                current_review = rating_match.group(2) if len(rating_match.groups()) > 1 else line
            else:
                # Continue current review
                if current_review:
                    current_review += " " + line
                else:
                    # Check if this looks like a review
                    if self._is_likely_review(line):
                        current_review = line

        # Don't forget the last review
        if current_review and current_rating:
            reviews.append({
                'review_text': current_review.strip(),
                'rating': self._normalize_rating(current_rating),
                'reviewer_name': self._extract_reviewer_name(current_review),
                'review_date': self._extract_review_date(current_review),
                'source_url': source_url
            })

        return reviews

    def _extract_product_info(self, url: str) -> Dict:
        """Extract basic product information from URL."""
        try:
            parsed = urlparse(url)
            path_parts = parsed.path.split('/')

            # Try to extract product name from path
            product_name = None
            for part in path_parts:
                if len(part) > 3 and not part.isdigit():
                    product_name = part.replace('-', ' ').replace('_', ' ')
                    break

            # Try to extract brand from common patterns
            brand = None
            if 'amazon' in parsed.netloc:
                brand_match = re.search(r'/dp/([A-Z0-9]+)', url)
                if brand_match:
                    brand = "Amazon Product"

            return {
                'name': product_name,
                'brand': brand,
                'domain': parsed.netloc
            }
        except:
            return {'name': None, 'brand': None, 'domain': None}

    def _normalize_rating(self, rating: str) -> Optional[float]:
        """Normalize rating to 1-5 scale."""
        try:
            # Extract numeric rating
            rating_match = re.search(r'(\d+(?:\.\d+)?)', str(rating))
            if rating_match:
                rating_value = float(rating_match.group(1))

                # Convert to 1-5 scale if needed
                if rating_value > 5:
                    rating_value = rating_value / 20  # Convert from 1-100 scale
                elif rating_value <= 1:
                    rating_value = rating_value * 5  # Convert from 0-1 scale

                return max(1, min(5, rating_value))
        except:
            pass
        return None

    def _extract_reviewer_name(self, review_text: str) -> Optional[str]:
        """Extract reviewer name from review text."""
        patterns = [
            r'by\s+([A-Z][a-z]+\s+[A-Z][a-z]+)',
            r'-\s*([A-Z][a-z]+\s+[A-Z][a-z]+)',
            r'([A-Z][a-z]+\s+[A-Z][a-z]+)\s*said',
        ]

        for pattern in patterns:
            match = re.search(pattern, review_text)
            if match:
                return match.group(1)

        return None

    def _extract_review_date(self, review_text: str) -> Optional[str]:
        """Extract review date from review text."""
        patterns = [
            r'(\d{1,2}/\d{1,2}/\d{4})',
            r'(\d{1,2}-\d{1,2}-\d{4})',
            r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}',
            r'(\d{1,2}\s+(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4})'
        ]

        for pattern in patterns:
            match = re.search(pattern, review_text, re.IGNORECASE)
            if match:
                return match.group(1)

        return None

    def _is_likely_review(self, text: str) -> bool:
        """Check if text is likely a review."""
        review_indicators = [
            'great', 'good', 'bad', 'excellent', 'poor', 'love', 'hate',
            'recommend', 'quality', 'price', 'service', 'delivery',
            'package', 'product', 'item', 'worked', 'didn\'t work'
        ]

        text_lower = text.lower()
        indicator_count = sum(1 for indicator in review_indicators if indicator in text_lower)

        # Also check length and sentence structure
        word_count = len(text.split())

        return (indicator_count >= 2 and word_count >= 10) or (indicator_count >= 1 and word_count >= 20)

    def get_product_reviews(self, product_url: str, max_pages: int = 5) -> List[Dict]:
        """Get all reviews for a product."""
        all_reviews = []

        # Search for review pages
        review_urls = self.search_reviews(product_url, max_pages)

        if not review_urls:
            # Try to scrape the product page directly for reviews
            scraped = self.scrape_reviews(product_url)
            if scraped['success']:
                reviews = self.extract_reviews_from_content(scraped['content'], product_url)
                all_reviews.extend(reviews)
        else:
            # Scrape each review URL
            for review_url in review_urls[:max_pages]:
                scraped = self.scrape_reviews(review_url)
                if scraped['success']:
                    reviews = self.extract_reviews_from_content(scraped['content'], review_url)
                    all_reviews.extend(reviews)

        # Remove duplicates based on review text similarity
        unique_reviews = []
        seen_texts = set()

        for review in all_reviews:
            review_text = review.get('review_text', '').strip()
            if review_text and len(review_text) > 20:
                # Simple deduplication based on first 100 characters
                text_key = review_text[:100].lower()
                if text_key not in seen_texts:
                    seen_texts.add(text_key)
                    unique_reviews.append(review)

        return unique_reviews