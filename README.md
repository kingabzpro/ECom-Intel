# 🔍 ECom Intel - Product Review Analyzer

A powerful Python application that analyzes product reviews using Firecrawl for web scraping and OpenAI GPT-4o-mini for AI-powered insights. Features a beautiful Streamlit dashboard with caching capabilities.

<img width="1805" height="804" alt="image" src="https://github.com/user-attachments/assets/cc80c734-d041-48d1-af95-90ebda530dda" />


## ✨ Features

- **🌐 Web Scraping**: Uses Firecrawl to search and scrape product reviews from multiple sources
- **🤖 AI Analysis**: Leverages OpenAI GPT-4o-mini for sentiment analysis and insights generation
- **💾 Data Caching**: SQLite database stores results to avoid repeated API calls
- **📊 Interactive Dashboard**: Beautiful Streamlit interface with charts and visualizations
- **⚡ Real-time Progress**: Live tracking of scraping and analysis progress
- **🔍 Smart Insights**: Extracts pros, cons, key themes, and actionable recommendations



## 🛠️ Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-username/ECom-Intel.git
   cd ECom-Intel
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   ```bash
   cp .env.example .env
   ```

   Edit the `.env` file and add your API keys:
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   FIRECRAWL_API_KEY=your_firecrawl_api_key_here
   DATABASE_PATH=reviews.db
   ```

## 🚀 Usage

1. **Start the Streamlit app**
   ```bash
   streamlit run app.py
   ```

2. **Open your browser** and navigate to `http://localhost:8501`

3. **Enter a product URL** (Amazon, eBay, or other e-commerce sites)

4. **Click "Analyze Reviews"** and watch the magic happen!

## 📁 Project Structure

```
ECom-Intel/
├── app.py              # Main Streamlit application
├── database.py         # SQLite database operations
├── firecrawl_client.py # Firecrawl integration
├── review_analyzer.py  # OpenAI analysis logic
├── requirements.txt    # Python dependencies
├── .env.example       # Environment variables template
└── README.md          # Project documentation
```

## 🔧 Configuration

### Required API Keys

1. **OpenAI API Key** - For sentiment analysis and insights generation
   - Get yours at: https://platform.openai.com/api-keys
   - Model used: `gpt-4o-mini` (cost-effective and fast)

2. **Firecrawl API Key** - For web scraping
   - Get yours at: https://www.firecrawl.dev/
   - Handles search, scraping, and content extraction

### Environment Variables

Create a `.env` file with the following variables:

```env
OPENAI_API_KEY=sk-your-openai-key
FIRECRAWL_API_KEY=fc-your-firecrawl-key
DATABASE_PATH=reviews.db
```

## 📊 Features Overview

### Data Collection
- **Smart Search**: Finds review pages related to the product
- **Multi-source Scraping**: Extracts reviews from various websites
- **Duplicate Detection**: Avoids processing the same reviews multiple times
- **Rate Limiting**: Respects website policies and API limits

### AI Analysis
- **Sentiment Analysis**: Categorizes reviews as positive, negative, or neutral
- **Insight Extraction**: Identifies key themes and patterns
- **Pros/Cons Analysis**: Summarizes what customers love and hate
- **Recommendations**: Provides actionable insights for improvement

### Dashboard Features
- **Real-time Progress**: Live updates during scraping and analysis
- **Interactive Charts**: Sentiment distribution and rating breakdowns
- **Review Samples**: Browse individual reviews with sentiment labels
- **Recent Analyses**: History of analyzed products
- **Caching Toggle**: Option to use cached results for faster analysis

## 🎯 Supported Websites

Works best with:
- Amazon products
- eBay listings
- Major e-commerce platforms
- Review websites

The application intelligently searches for reviews related to any product URL you provide.

## 💡 Tips for Best Results

1. **Use direct product URLs** for better accuracy
2. **Popular products** typically have more reviews available
3. **Check cached results** first to save API credits
4. **Adjust the max pages** slider based on your needs
5. **Allow sufficient time** for comprehensive analysis

## 🔒 Privacy & Security

- All data is stored locally in SQLite database
- No data is shared with third parties
- API keys are kept secure via environment variables
- Reviews are processed anonymously

## 🐛 Troubleshooting

### Common Issues

1. **"API Key Not Found" Error**
   - Ensure `.env` file exists with correct API keys
   - Check that API keys are valid and active

2. **"No Reviews Found"**
   - Try a different product URL
   - Check if the product has reviews available
   - Increase the max pages setting

3. **"Scraping Failed"**
   - Verify Firecrawl API key is valid
   - Check internet connection
   - Some websites may block scraping

4. **"Analysis Error"**
   - Verify OpenAI API key and credits
   - Check if the model is available
   - Try again with fewer reviews

### Getting Help

- Check the [Issues](https://github.com/your-username/ECom-Intel/issues) page
- Review API documentation for [OpenAI](https://platform.openai.com/docs) and [Firecrawl](https://docs.firecrawl.dev/)
- Contact support if needed

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the project
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Firecrawl](https://firecrawl.dev/) - Powerful web scraping API
- [OpenAI](https://openai.com/) - AI language models
- [Streamlit](https://streamlit.io/) - Beautiful data apps
- [Plotly](https://plotly.com/) - Interactive charts

## 📈 Future Enhancements

- [ ] Support for more e-commerce platforms
- [ ] Product comparison feature
- [ ] Export results to PDF/CSV
- [ ] Email notifications for analysis completion
- [ ] Multi-language support
- [ ] Advanced filtering options
- [ ] Trend analysis over time

---

**Made with ❤️ by Abid**
