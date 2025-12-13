# Food Price Predictor

A web application for predicting agricultural commodity prices in Kenya using machine learning.

## Features

- User authentication and authorization
- Price prediction using machine learning models
- Interactive dashboard with historical data
- Market trends analysis
- Contact form with email notifications
- Mobile-responsive design

## Setup Instructions

### Prerequisites

- Python 3.8 or higher
- pip (Python package installer)
- Virtual environment (recommended)

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd food_price_project
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
Create a `.env` file in the project root with:
```
SECRET_KEY=your-secret-key
DEBUG=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
```

5. Run migrations:
```bash
python manage.py makemigrations
python manage.py migrate
```

6. Create a superuser:
```bash
python manage.py createsuperuser
```

7. Run the development server:
```bash
python manage.py runserver
```

### Production Deployment

1. Update settings.py:
- Set `DEBUG = False`
- Update `ALLOWED_HOSTS` with your domain
- Configure your production database
- Set up proper security settings

2. Collect static files:
```bash
python manage.py collectstatic
```

3. Deploy using Gunicorn:
```bash
gunicorn food_price_project.wsgi:application
```

## Mobile App Development

The web application is designed to be mobile-responsive and can be converted into a mobile app using:

1. Progressive Web App (PWA) approach
2. React Native or Flutter for native mobile apps
3. API endpoints for mobile app integration

## API Endpoints

- `/api/auth/` - Authentication endpoints
- `/api/predict/` - Price prediction endpoints
- `/api/market-trends/` - Market trends data
- `/api/contact/` - Contact form submission

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contact

For support or queries, contact:
- Email: obernard377@gmail.com
- Phone: +254 742 423 200 