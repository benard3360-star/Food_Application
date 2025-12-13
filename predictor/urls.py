from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from .api import UserRegistrationView, UserLoginView, PredictionViewSet, contact_api
import logging

logger = logging.getLogger(__name__)

router = DefaultRouter()
router.register(r'predictions', PredictionViewSet, basename='prediction')

# Debug function to log URL patterns
def log_url_patterns():
    logger.info("Available URL patterns:")
    for pattern in urlpatterns:
        if hasattr(pattern, 'callback'):
            logger.info(f"URL Pattern: {pattern.pattern} -> {pattern.callback.__name__}")
        elif hasattr(pattern, 'urlconf_name'):
            logger.info(f"URL Pattern: {pattern.pattern} -> include({pattern.urlconf_name})")

urlpatterns = [
    path('', views.home, name='home'),  # This will serve food5.html at the root URL
    path('market-trends/', views.market_trends, name='market_trends'),
    path('contact/', views.contact_view, name='contact'),
    path('predict/', views.make_prediction, name='make_prediction'),
    path('download-predictions/', views.download_predictions, name='download_predictions'),
    path('notify/', views.notify_user, name='notify_user'),
    path('test-twilio/', views.test_twilio, name='test_twilio'),

    # New feature pages
    path('cheapest-market/', views.cheapest_market, name='cheapest_market'),
    path('alerts/', views.alerts, name='alerts'),
    path('community-reporting/', views.community_reporting, name='community_reporting'),
    path('budget-estimator/', views.budget_estimator, name='budget_estimator'),
    path('nutrition-tips/', views.nutrition_tips, name='nutrition_tips'),
    path('planting-selling-suggestions/', views.planting_selling_suggestions, name='planting_selling_suggestions'),
    path('impact-dashboard/', views.impact_dashboard, name='impact_dashboard'),
    path('set-language/', views.set_language, name='set_language'),
    path('download-community-reports/', views.download_community_reports, name='download_community_reports'),
    
    # API endpoints
    path('api/', include(router.urls)),
    path('api/register/', UserRegistrationView.as_view(), name='api_register'),
    path('api/login/', UserLoginView.as_view(), name='api_login'),
    path('api/contact/', contact_api, name='api_contact'),
    path('api/chatbot/', views.chatbot_api, name='chatbot_api'),
    path('api/market-data/', views.market_data_api, name='market_data_api'),
]

# Log URL patterns on startup
try:
    log_url_patterns()
except Exception as e:
    logger.error(f"Error logging URL patterns: {str(e)}")
