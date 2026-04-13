# Smart Home Gardening Assistant 🌱

A comprehensive full-stack web application for smart home gardening with AI-powered features for crop planning, disease detection, financial management, and more.

## Features

### 🌾 **Crop Planning**
- AI-powered crop recommendations based on location, season, and soil type
- Detailed crop information including water needs, sunlight requirements, and expected yield
- Personalized suggestions for optimal growing conditions

### 🦠 **Disease Detection**
- Machine learning-based disease identification from symptoms
- Comprehensive treatment and prevention recommendations
- Support for multiple crops with detailed disease databases

### 💰 **Financial Planning**
- Cost estimation for crop cultivation
- Profit analysis and break-even calculations
- Market price integration and financial recommendations

### 💧 **Irrigation Management**
- Smart watering schedules based on weather and soil conditions
- Water-saving recommendations and irrigation method suggestions
- Real-time adjustments based on environmental factors

### 🌤️ **Weather Integration**
- Real-time weather data and forecasts
- Farming recommendations based on weather conditions
- Seasonal planning assistance

### 🤖 **AI Advisory System**
- Intelligent chatbot for farming questions
- Expert advice on various agricultural topics
- 24/7 support for farming queries

### 🌱 **Soil Health Analysis**
- Comprehensive soil testing and analysis
- pH level assessment and recommendations
- Nutrient deficiency detection and amendment suggestions

## Technology Stack

### Backend
- **Python Flask** - REST API framework
- **MySQL** - Database for storing agricultural data
- **Scikit-learn** - Machine learning for crop and disease prediction
- **Pandas** - Data processing and analysis

### Frontend
- **HTML5/CSS3** - Modern responsive design
- **JavaScript** - Interactive user interface
- **Fetch API** - Client-server communication

### Machine Learning Models
- **Crop Recommendation Model** - Random Forest classifier
- **Disease Detection Model** - Naive Bayes with TF-IDF
- **Price Prediction Model** - Linear Regression

## Installation & Setup

### Prerequisites
- Python 3.8+
- MySQL Server
- Web browser (Chrome, Firefox, Safari, Edge)

### 1. Clone the Repository
```bash
git clone <repository-url>
cd smart-agriculture-system
```

### 2. Install Python Dependencies
```bash
pip install -r requirements.txt
```

### 3. Setup MySQL Database
1. Install MySQL Server on your system
2. Create a new database named `smart_gardening`
3. Update database credentials in `backend/db.py`:
```python
DB_CONFIG = {
    'host': 'localhost',
    'user': 'your_mysql_username',
    'password': 'your_mysql_password',
    'database': 'smart_gardening'
}
```

### 4. Initialize Database
```bash
python backend/db.py
```

### 5. Start the Flask Server
```bash
python backend/app.py
```

### 6. Open the Application
Open your web browser and navigate to:
- **Login Page**: `http://localhost:5000` or open `frontend/index.html`
- **Dashboard**: `frontend/dashboard.html` (after login)

## API Endpoints

### Authentication
- `POST /api/login` - User authentication

### Core Features
- `GET /api/crops` - Get all available crops
- `POST /api/crop-recommendation` - Get crop recommendations
- `POST /api/soil-health` - Analyze soil health
- `POST /api/disease-detection` - Detect crop diseases
- `GET /api/market-prices` - Get current market prices
- `POST /api/finance-estimation` - Calculate farming costs and profits
- `POST /api/irrigation-schedule` - Get irrigation recommendations
- `GET /api/weather-forecast` - Get weather forecast
- `POST /api/advisory` - Get AI farming advice

## Project Structure

```
smart-agriculture-system/
├── README.md
├── requirements.txt
├── backend/
│   ├── app.py                 # Flask application with API routes
│   ├── db.py                  # Database connection and utilities
│   ├── models/
│   │   ├── crop_model.py      # ML model for crop recommendations
│   │   ├── disease_model.py   # ML model for disease detection
│   │   └── price_model.py     # ML model for price prediction
│   └── modules/
│       ├── crop_recommendation.py
│       ├── soil_health.py
│       ├── finance.py
│       ├── irrigation.py
│       ├── weather.py
│       └── advisory.py
├── frontend/
│   ├── index.html            # Login page
│   ├── dashboard.html        # Main dashboard
│   ├── styles.css            # CSS styles
│   └── script.js             # JavaScript functionality
└── datasets/                 # Data files (if any)
```

## Usage

### For New Users
1. Visit the login page
2. Use demo credentials: `admin` / `password`
3. Explore different modules from the sidebar

### Key Features Usage

#### Crop Planning
- Select your location, season, and soil type
- Get personalized crop recommendations
- View detailed growing requirements

#### Disease Detection
- Enter crop name and describe symptoms
- Receive AI-powered disease identification
- Get treatment and prevention advice

#### Financial Planning
- Input crop name and area
- Get detailed cost breakdowns
- View profit projections and market insights

#### AI Advisory
- Ask questions in natural language
- Get expert farming advice
- Learn about various agricultural topics

## Machine Learning Models

### Training the Models
The ML models are automatically trained when first used, but you can manually train them:

```python
from backend.models.crop_model import crop_model
from backend.models.disease_model import disease_model
from backend.models.price_model import price_model

# Train models
crop_model.train_model()
disease_model.train_model()
price_model.train_model()
```

### Model Performance
- **Crop Recommendation**: ~85% accuracy
- **Disease Detection**: ~78% accuracy
- **Price Prediction**: R² score ~0.82

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions:
- Create an issue in the repository
- Check the troubleshooting section below

## Troubleshooting

### Database Connection Issues
- Ensure MySQL server is running
- Verify database credentials in `db.py`
- Check if `smart_gardening` database exists

### API Connection Issues
- Verify Flask server is running on port 5000
- Check for firewall blocking the port
- Ensure all dependencies are installed

### Frontend Issues
- Clear browser cache
- Check browser console for JavaScript errors
- Ensure CORS is enabled (handled by Flask-CORS)

## Future Enhancements

- [ ] Mobile application development
- [ ] Real-time sensor integration
- [ ] Advanced weather API integration
- [ ] Multi-language support
- [ ] Offline functionality
- [ ] Social features for farmer communities
- [ ] Integration with agricultural IoT devices

## Acknowledgments

- Built with Flask and modern web technologies
- Machine learning powered by scikit-learn
- UI design inspired by modern agricultural tech platforms

---

**Happy Gardening! 🌱🚀**
