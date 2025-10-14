import os
import json
from typing import List, Dict, Optional
from collections import Counter
import openai
from dotenv import load_dotenv

load_dotenv()

class ReviewAnalyzer:
    def __init__(self):
        self.client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        if not self.client.api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")

    def analyze_reviews(self, reviews: List[Dict]) -> Dict:
        """Analyze reviews and provide comprehensive insights."""
        if not reviews:
            return {
                'total_reviews': 0,
                'average_rating': 0.0,
                'sentiment_distribution': {'positive': 0, 'negative': 0, 'neutral': 0},
                'key_insights': [],
                'pros': [],
                'cons': [],
                'rating_summary': {},
                'recommendations': []
            }

        # Perform sentiment analysis on each review
        analyzed_reviews = []
        for review in reviews:
            sentiment_result = self._analyze_sentiment(review.get('review_text', ''))
            review.update(sentiment_result)
            analyzed_reviews.append(review)

        # Calculate overall metrics
        total_reviews = len(analyzed_reviews)
        ratings = [r.get('rating') for r in analyzed_reviews if r.get('rating') is not None]
        average_rating = sum(ratings) / len(ratings) if ratings else 0.0

        # Get sentiment distribution
        sentiment_distribution = self._calculate_sentiment_distribution(analyzed_reviews)

        # Generate insights using AI
        insights = self._generate_insights(analyzed_reviews)

        return {
            'total_reviews': total_reviews,
            'average_rating': round(average_rating, 2),
            'sentiment_distribution': sentiment_distribution,
            'key_insights': insights.get('key_insights', []),
            'pros': insights.get('pros', []),
            'cons': insights.get('cons', []),
            'rating_summary': self._calculate_rating_summary(ratings),
            'recommendations': insights.get('recommendations', [])
        }

    def _analyze_sentiment(self, text: str) -> Dict:
        """Analyze sentiment of a single review."""
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "Analyze the sentiment of the following review. Return a JSON object with 'sentiment' (positive, negative, or neutral) and 'score' (0-1, where 0 is very negative and 1 is very positive)."
                    },
                    {
                        "role": "user",
                        "content": f"Review: {text}"
                    }
                ],
                response_format={"type": "json_object"}
            )

            result = json.loads(response.choices[0].message.content)
            return {
                'sentiment_label': result.get('sentiment', 'neutral'),
                'sentiment_score': result.get('score', 0.5)
            }

        except Exception as e:
            print(f"Sentiment analysis error: {str(e)}")
            return {
                'sentiment_label': 'neutral',
                'sentiment_score': 0.5
            }

    def _generate_insights(self, reviews: List[Dict]) -> Dict:
        """Generate comprehensive insights from reviews."""
        # Prepare reviews text for analysis
        reviews_text = "\n".join([
            f"Review {i+1}: {review.get('review_text', '')} (Rating: {review.get('rating', 'N/A')})"
            for i, review in enumerate(reviews[:50])  # Limit to first 50 reviews for token limit
        ])

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": """You are an expert product analyst. Analyze the following product reviews and provide insights in JSON format:
                        {
                            "key_insights": ["insight 1", "insight 2", ...],
                            "pros": ["pro 1", "pro 2", ...],
                            "cons": ["con 1", "con 2", ...],
                            "recommendations": ["recommendation 1", "recommendation 2", ...]
                        }

                        Focus on:
                        - Key themes and patterns
                        - Most praised features
                        - Common complaints
                        - Actionable recommendations
                        Keep insights concise and specific."""
                    },
                    {
                        "role": "user",
                        "content": f"Analyze these product reviews:\n\n{reviews_text}"
                    }
                ],
                response_format={"type": "json_object"}
            )

            return json.loads(response.choices[0].message.content)

        except Exception as e:
            print(f"Insights generation error: {str(e)}")
            return {
                'key_insights': ['Unable to generate insights automatically'],
                'pros': [],
                'cons': [],
                'recommendations': []
            }

    def _calculate_sentiment_distribution(self, reviews: List[Dict]) -> Dict:
        """Calculate sentiment distribution from reviews."""
        sentiments = [r.get('sentiment_label', 'neutral') for r in reviews]
        sentiment_counts = Counter(sentiments)
        total = len(sentiments)

        return {
            'positive': round((sentiment_counts.get('positive', 0) / total) * 100, 1) if total > 0 else 0,
            'negative': round((sentiment_counts.get('negative', 0) / total) * 100, 1) if total > 0 else 0,
            'neutral': round((sentiment_counts.get('neutral', 0) / total) * 100, 1) if total > 0 else 0
        }

    def _calculate_rating_summary(self, ratings: List[float]) -> Dict:
        """Calculate rating distribution and statistics."""
        if not ratings:
            return {}

        rating_counts = Counter([int(r) for r in ratings if r])
        total_ratings = len(ratings)

        return {
            '5_star': round((rating_counts.get(5, 0) / total_ratings) * 100, 1),
            '4_star': round((rating_counts.get(4, 0) / total_ratings) * 100, 1),
            '3_star': round((rating_counts.get(3, 0) / total_ratings) * 100, 1),
            '2_star': round((rating_counts.get(2, 0) / total_ratings) * 100, 1),
            '1_star': round((rating_counts.get(1, 0) / total_ratings) * 100, 1),
            'total_ratings': total_ratings
        }

    def get_review_summary(self, product_title: str, reviews: List[Dict]) -> str:
        """Generate a human-readable summary of reviews."""
        if not reviews:
            return f"No reviews found for {product_title}."

        analysis = self.analyze_reviews(reviews)

        summary = f"""
## Product Review Summary: {product_title}

**Overall Rating:** {analysis['average_rating']}/5.0 ({analysis['total_reviews']} reviews)

**Sentiment Breakdown:**
- Positive: {analysis['sentiment_distribution']['positive']}%
- Neutral: {analysis['sentiment_distribution']['neutral']}%
- Negative: {analysis['sentiment_distribution']['negative']}%

**Key Insights:**
{chr(10).join(f"• {insight}" for insight in analysis['key_insights'][:5])}

**What Customers Love:**
{chr(10).join(f"• {pro}" for pro in analysis['pros'][:5])}

**Common Complaints:**
{chr(10).join(f"• {con}" for con in analysis['cons'][:5])}

**Recommendations:**
{chr(10).join(f"• {rec}" for rec in analysis['recommendations'][:3])}
        """.strip()

        return summary

    def compare_products(self, product_analyses: Dict[str, Dict]) -> Dict:
        """Compare multiple products based on their review analyses."""
        if len(product_analyses) < 2:
            return {"error": "Need at least 2 products to compare"}

        try:
            comparison_data = []
            for product_name, analysis in product_analyses.items():
                comparison_data.append({
                    "name": product_name,
                    "rating": analysis.get('average_rating', 0),
                    "total_reviews": analysis.get('total_reviews', 0),
                    "positive_sentiment": analysis.get('sentiment_distribution', {}).get('positive', 0),
                    "key_pros": analysis.get('pros', [])[:3],
                    "key_cons": analysis.get('cons', [])[:3]
                })

            # Generate comparison insights
            comparison_prompt = f"""
            Compare these products based on their review analysis:
            {json.dumps(comparison_data, indent=2)}

            Provide a JSON comparison with:
            {{
                "best_overall": "product name",
                "best_value": "product name",
                "highest_quality": "product name",
                "comparison_points": ["point 1", "point 2", ...],
                "recommendation": "which product and why"
            }}
            """

            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a product comparison expert. Provide objective analysis based on the provided data."
                    },
                    {
                        "role": "user",
                        "content": comparison_prompt
                    }
                ],
                response_format={"type": "json_object"}
            )

            comparison_result = json.loads(response.choices[0].message.content)
            comparison_result['product_data'] = comparison_data

            return comparison_result

        except Exception as e:
            print(f"Comparison error: {str(e)}")
            return {"error": "Unable to generate comparison"}