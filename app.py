import time
from urllib.parse import urlparse

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from database import ReviewDatabase
from firecrawl_client import FirecrawlClient
from review_analyzer import ReviewAnalyzer

# Configure Streamlit page
st.set_page_config(
    page_title="ECom Intel - Product Review Analyzer",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for better styling
st.markdown(
    """
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .insight-box {
        background-color: #e8f4f8;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #00cc96;
        margin: 0.5rem 0;
    }
    .warning-box {
        background-color: #fff3cd;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #ffc107;
        margin: 0.5rem 0;
    }
    .error-box {
        background-color: #f8d7da;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #dc3545;
        margin: 0.5rem 0;
    }
</style>
""",
    unsafe_allow_html=True,
)


def validate_url(url: str) -> bool:
    """Validate if the URL is properly formatted."""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False


def extract_product_name(url: str) -> str:
    """Extract product name from URL."""
    try:
        parsed = urlparse(url)
        path_parts = [part for part in parsed.path.split("/") if part and len(part) > 2]
        if path_parts:
            return path_parts[-1].replace("-", " ").replace("_", " ").title()
        return "Unknown Product"
    except Exception:
        return "Unknown Product"


def create_sentiment_chart(sentiment_data: dict) -> go.Figure:
    """Create sentiment distribution pie chart."""
    fig = go.Figure(
        data=[
            go.Pie(
                labels=list(sentiment_data.keys()),
                values=list(sentiment_data.values()),
                hole=0.3,
                marker_colors=["#00cc96", "#ff6692", "#636efa"],
            )
        ]
    )
    fig.update_layout(
        title="Sentiment Distribution", font=dict(size=14), showlegend=True, height=400
    )
    return fig


def create_rating_chart(rating_data: dict) -> go.Figure:
    """Create rating distribution bar chart."""
    ratings = ["5★", "4★", "3★", "2★", "1★"]
    values = [
        rating_data.get("5_star", 0),
        rating_data.get("4_star", 0),
        rating_data.get("3_star", 0),
        rating_data.get("2_star", 0),
        rating_data.get("1_star", 0),
    ]

    fig = go.Figure(
        data=[
            go.Bar(
                x=ratings,
                y=values,
                marker_color=["#00cc96", "#00cc96", "#ffab00", "#ff6692", "#ff6692"],
                text=[f"{v}%" for v in values],
                textposition="auto",
            )
        ]
    )
    fig.update_layout(
        title="Rating Distribution",
        xaxis_title="Rating",
        yaxis_title="Percentage (%)",
        height=400,
    )
    return fig


def main():
    # Initialize components
    try:
        db = ReviewDatabase()
        firecrawl_client = FirecrawlClient()
        analyzer = ReviewAnalyzer()
    except Exception as e:
        st.error(f"⚠️ **Initialization Error**: {str(e)}")
        st.error(
            "Please check your environment variables and API keys in the `.env` file."
        )
        return

    # Header
    st.markdown(
        '<h1 class="main-header">🔍 ECom Intel - Product Review Analyzer</h1>',
        unsafe_allow_html=True,
    )
    st.markdown("---")

    # Sidebar
    st.sidebar.title("🚀 Analysis Settings")
    st.sidebar.markdown(
        "Enter a product URL to analyze customer reviews and get AI-powered insights."
    )

    # URL Input
    product_url = st.sidebar.text_input(
        "Product URL",
        placeholder="https://www.amazon.com/dp/PRODUCT_ID",
        help="Enter the URL of the product you want to analyze",
    )

    # Analysis options
    max_pages = st.sidebar.slider("Max review pages to scrape", 1, 10, 5)
    include_cached = st.sidebar.checkbox("Use cached results if available", value=True)

    # Main content area
    if st.sidebar.button("🔍 Analyze Reviews", type="primary"):
        if not product_url:
            st.sidebar.error("Please enter a product URL")
            return

        if not validate_url(product_url):
            st.sidebar.error("Please enter a valid URL")
            return

        # Start analysis
        product_name = extract_product_name(product_url)
        st.success(f"🎯 Analyzing reviews for: **{product_name}**")

        # Check for cached results
        cached_analysis = None
        if include_cached:
            with st.spinner("🔍 Checking for cached results..."):
                # Try to find existing product in database
                recent_products = db.get_recent_products(50)
                for product in recent_products:
                    if product["url"] == product_url:
                        cached_analysis = db.get_analysis(product["id"])
                        if cached_analysis:
                            product_info = db.get_product_info(product["id"])
                            reviews = db.get_reviews(product["id"])
                            break

        if cached_analysis:
            st.info("✅ Using cached results. Analysis completed in seconds!")
            analysis_result = cached_analysis
            product_info = product_info
            reviews = reviews
        else:
            # Perform fresh analysis
            progress_bar = st.progress(0)
            status_text = st.empty()

            try:
                # Step 1: Get product info
                status_text.text("🔍 Searching for reviews...")
                progress_bar.progress(20)
                time.sleep(1)

                # Step 2: Scrape reviews
                status_text.text("📥 Scraping review content...")
                progress_bar.progress(40)
                reviews = firecrawl_client.get_product_reviews(product_url, max_pages)

                if not reviews:
                    st.error(
                        "❌ No reviews found for this product. Please try a different URL."
                    )
                    return

                status_text.text(f"📊 Found {len(reviews)} reviews")
                progress_bar.progress(60)

                # Step 3: Analyze reviews
                status_text.text("🧠 Analyzing reviews with AI...")
                progress_bar.progress(80)
                analysis_result = analyzer.analyze_reviews(reviews)

                # Step 4: Save to database
                status_text.text("💾 Saving results...")
                progress_bar.progress(90)

                product_id = db.get_or_create_product(
                    url=product_url, title=product_name
                )
                db.add_reviews(product_id, reviews)
                db.save_analysis(product_id, analysis_result)

                product_info = db.get_product_info(product_id)

                progress_bar.progress(100)
                status_text.text("✅ Analysis complete!")
                time.sleep(1)

                # Clear progress indicators
                progress_bar.empty()
                status_text.empty()

            except Exception as e:
                st.error(f"❌ **Analysis Error**: {str(e)}")
                return

        # Display results
        st.markdown("---")
        st.header("📊 Analysis Results")

        # Key metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Reviews", analysis_result["total_reviews"])
        with col2:
            st.metric("Average Rating", f"{analysis_result['average_rating']}/5.0")
        with col3:
            st.metric(
                "Positive Sentiment",
                f"{analysis_result['sentiment_distribution']['positive']}%",
            )
        with col4:
            st.metric(
                "Negative Sentiment",
                f"{analysis_result['sentiment_distribution']['negative']}%",
            )

        # Charts
        col1, col2 = st.columns(2)
        with col1:
            fig_sentiment = create_sentiment_chart(
                analysis_result["sentiment_distribution"]
            )
            st.plotly_chart(fig_sentiment, width="stretch")
        with col2:
            fig_rating = create_rating_chart(analysis_result["rating_summary"])
            st.plotly_chart(fig_rating, width="stretch")

        # Key Insights
        st.markdown("---")
        st.header("💡 Key Insights")
        if analysis_result.get("key_insights"):
            for insight in analysis_result.get("key_insights", []):
                st.markdown(
                    f'<div class="insight-box">• {insight}</div>',
                    unsafe_allow_html=True,
                )
        else:
            st.info("No key insights available")

        # Pros and Cons
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("✅ What Customers Love")
            if analysis_result.get("pros"):
                for pro in analysis_result.get("pros", []):
                    st.markdown(
                        f'<div class="insight-box">✓ {pro}</div>',
                        unsafe_allow_html=True,
                    )
            else:
                st.info("No positive feedback identified")

        with col2:
            st.subheader("⚠️ Common Complaints")
            if analysis_result.get("cons"):
                for con in analysis_result.get("cons", []):
                    st.markdown(
                        f'<div class="warning-box">⚠ {con}</div>',
                        unsafe_allow_html=True,
                    )
            else:
                st.info("No negative feedback identified")

        # Recommendations
        if analysis_result.get("recommendations"):
            st.markdown("---")
            st.header("🎯 Recommendations")
            for rec in analysis_result.get("recommendations", []):
                st.markdown(
                    f'<div class="insight-box">💡 {rec}</div>', unsafe_allow_html=True
                )

        # Recent Reviews Sample
        if reviews:
            st.markdown("---")
            st.header("📝 Sample Reviews")
            sample_reviews = reviews[:5]  # Show first 5 reviews

            for i, review in enumerate(sample_reviews, 1):
                with st.expander(
                    f"Review {i} - Rating: {review.get('rating', 'N/A')}/5"
                ):
                    st.write(f"**Review:** {review.get('review_text', 'N/A')}")
                    if review.get("reviewer_name"):
                        st.write(f"**Reviewer:** {review.get('reviewer_name')}")
                    if review.get("review_date"):
                        st.write(f"**Date:** {review.get('review_date')}")
                    if review.get("sentiment_label"):
                        sentiment = review.get("sentiment_label", "neutral")
                        sentiment_color = {
                            "positive": "🟢",
                            "negative": "🔴",
                            "neutral": "🟡",
                        }.get(sentiment, "⚪")
                        st.write(
                            f"**Sentiment:** {sentiment_color} {sentiment.title()}"
                        )

    # Recent Analyses
    st.markdown("---")
    st.header("🕐 Recent Analyses")

    recent_products = db.get_recent_products(10)
    if recent_products:
        df = pd.DataFrame(recent_products)
        df = df.copy()
        df.loc[:, "average_rating"] = df["average_rating"].round(2)
        display_df = df[
            ["title", "brand", "total_reviews", "average_rating", "created_at"]
        ]
        display_df.columns = ["Product", "Brand", "Reviews", "Rating", "Analyzed"]
        display_df.loc[:, "Analyzed"] = pd.to_datetime(
            display_df["Analyzed"]
        ).dt.strftime("%Y-%m-%d %H:%M")
        st.dataframe(display_df, width="stretch")
    else:
        st.info("No recent analyses found. Start by analyzing a product!")

    # Footer
    st.markdown("---")
    st.markdown(
        """
    <div style='text-align: center; color: #666; padding: 20px;'>
        <p>ECom Intel - Powered by Firecrawl & OpenAI GPT-4o-mini</p>
        <p>Analyze product reviews to get AI-powered insights and recommendations</p>
    </div>
    """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
