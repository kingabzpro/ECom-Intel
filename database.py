import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Optional

class ReviewDatabase:
    def __init__(self, db_path: str = "reviews.db"):
        self.db_path = db_path
        self.init_database()

    def init_database(self):
        """Initialize the SQLite database with required tables."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Products table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS products (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    url TEXT UNIQUE NOT NULL,
                    title TEXT,
                    brand TEXT,
                    price TEXT,
                    image_url TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Reviews table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS reviews (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    product_id INTEGER,
                    review_text TEXT NOT NULL,
                    rating INTEGER,
                    reviewer_name TEXT,
                    review_date TEXT,
                    source_url TEXT,
                    sentiment_score REAL,
                    sentiment_label TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (product_id) REFERENCES products (id)
                )
            ''')

            # Analysis results table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS analysis (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    product_id INTEGER,
                    sentiment_distribution TEXT,
                    key_insights TEXT,
                    pros TEXT,
                    cons TEXT,
                    rating_summary TEXT,
                    total_reviews INTEGER,
                    average_rating REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (product_id) REFERENCES products (id)
                )
            ''')

            conn.commit()

    def get_or_create_product(self, url: str, title: str = None, brand: str = None,
                            price: str = None, image_url: str = None) -> int:
        """Get existing product or create new one."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Check if product exists
            cursor.execute('SELECT id FROM products WHERE url = ?', (url,))
            result = cursor.fetchone()

            if result:
                product_id = result[0]
                # Update product info if provided
                if title or brand or price or image_url:
                    cursor.execute('''
                        UPDATE products
                        SET title = COALESCE(?, title),
                            brand = COALESCE(?, brand),
                            price = COALESCE(?, price),
                            image_url = COALESCE(?, image_url),
                            updated_at = CURRENT_TIMESTAMP
                        WHERE id = ?
                    ''', (title, brand, price, image_url, product_id))
            else:
                # Create new product
                cursor.execute('''
                    INSERT INTO products (url, title, brand, price, image_url)
                    VALUES (?, ?, ?, ?, ?)
                ''', (url, title, brand, price, image_url))
                product_id = cursor.lastrowid

            conn.commit()
            return product_id

    def add_reviews(self, product_id: int, reviews: List[Dict]) -> int:
        """Add reviews to the database and avoid duplicates."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            added_count = 0

            for review in reviews:
                # Check if review already exists
                cursor.execute('''
                    SELECT id FROM reviews
                    WHERE product_id = ? AND review_text = ? AND reviewer_name = ?
                ''', (product_id, review.get('review_text', ''), review.get('reviewer_name', '')))

                if not cursor.fetchone():
                    cursor.execute('''
                        INSERT INTO reviews
                        (product_id, review_text, rating, reviewer_name, review_date,
                         source_url, sentiment_score, sentiment_label)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        product_id,
                        review.get('review_text', ''),
                        review.get('rating'),
                        review.get('reviewer_name'),
                        review.get('review_date'),
                        review.get('source_url'),
                        review.get('sentiment_score'),
                        review.get('sentiment_label')
                    ))
                    added_count += 1

            conn.commit()
            return added_count

    def save_analysis(self, product_id: int, analysis: Dict):
        """Save analysis results for a product."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Delete existing analysis for this product
            cursor.execute('DELETE FROM analysis WHERE product_id = ?', (product_id,))

            # Insert new analysis
            cursor.execute('''
                INSERT INTO analysis
                (product_id, sentiment_distribution, key_insights, pros, cons,
                 rating_summary, total_reviews, average_rating)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                product_id,
                json.dumps(analysis.get('sentiment_distribution', {})),
                json.dumps(analysis.get('key_insights', [])),
                json.dumps(analysis.get('pros', [])),
                json.dumps(analysis.get('cons', [])),
                json.dumps(analysis.get('rating_summary', {})),
                analysis.get('total_reviews', 0),
                analysis.get('average_rating', 0.0)
            ))

            conn.commit()

    def get_reviews(self, product_id: int) -> List[Dict]:
        """Get all reviews for a product."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT review_text, rating, reviewer_name, review_date,
                       sentiment_score, sentiment_label
                FROM reviews
                WHERE product_id = ?
                ORDER BY review_date DESC
            ''', (product_id,))

            reviews = []
            for row in cursor.fetchall():
                reviews.append({
                    'review_text': row[0],
                    'rating': row[1],
                    'reviewer_name': row[2],
                    'review_date': row[3],
                    'sentiment_score': row[4],
                    'sentiment_label': row[5]
                })

            return reviews

    def get_analysis(self, product_id: int) -> Optional[Dict]:
        """Get analysis results for a product."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT sentiment_distribution, key_insights, pros, cons,
                       rating_summary, total_reviews, average_rating
                FROM analysis
                WHERE product_id = ?
                ORDER BY created_at DESC
                LIMIT 1
            ''', (product_id,))

            result = cursor.fetchone()
            if result:
                return {
                    'sentiment_distribution': json.loads(result[0] or '{}'),
                    'key_insights': json.loads(result[1] or '[]'),
                    'pros': json.loads(result[2] or '[]'),
                    'cons': json.loads(result[3] or '[]'),
                    'rating_summary': json.loads(result[4] or '{}'),
                    'total_reviews': result[5],
                    'average_rating': result[6]
                }
            return None

    def get_product_info(self, product_id: int) -> Optional[Dict]:
        """Get product information."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT url, title, brand, price, image_url, created_at
                FROM products
                WHERE id = ?
            ''', (product_id,))

            result = cursor.fetchone()
            if result:
                return {
                    'url': result[0],
                    'title': result[1],
                    'brand': result[2],
                    'price': result[3],
                    'image_url': result[4],
                    'created_at': result[5]
                }
            return None

    def get_recent_products(self, limit: int = 10) -> List[Dict]:
        """Get recently analyzed products."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT p.id, p.url, p.title, p.brand, p.price, a.total_reviews,
                       a.average_rating, p.created_at
                FROM products p
                LEFT JOIN analysis a ON p.id = a.product_id
                ORDER BY p.created_at DESC
                LIMIT ?
            ''', (limit,))

            products = []
            for row in cursor.fetchall():
                products.append({
                    'id': row[0],
                    'url': row[1],
                    'title': row[2],
                    'brand': row[3],
                    'price': row[4],
                    'total_reviews': row[5] or 0,
                    'average_rating': row[6] or 0.0,
                    'created_at': row[7]
                })

            return products