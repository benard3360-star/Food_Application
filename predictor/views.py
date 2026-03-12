# predictor/views.py

from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from .models import Prediction, CommunityReport
from .utils import send_sms, format_phone_number
import joblib
import numpy as np
import os
import csv
import io
import datetime
import json
import logging
import traceback
from django.contrib import messages
from twilio.rest import Client
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
import requests
import openai
from decouple import config
from django.contrib.admin.views.decorators import staff_member_required
from django.utils import timezone
import pytz
import pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
import base64

logger = logging.getLogger(__name__)

# Path to models inside the predictor app
MODEL_DIR = os.path.join(settings.BASE_DIR, 'predictor', 'models')

# Full paths to the .pkl files
model_path = os.path.join(MODEL_DIR, 'final_model3_top10.pkl')
encoder_path = os.path.join(MODEL_DIR, 'encoders_dict.pkl')
features_path = os.path.join(MODEL_DIR, 'top_10_features2.pkl')

# Lazy load models to save memory
model = None
encoders = None
top_10_features = None

def load_models():
    global model, encoders, top_10_features
    if model is None:
        try:
            model = joblib.load(model_path)
            encoders = joblib.load(encoder_path)
            top_10_features = list(joblib.load(features_path))
        except Exception as e:
            logger.error(f"Error loading ML models: {str(e)}")
            # Fallback values
            top_10_features = ['Commodity', 'Region', 'Market', 'Month', 'Year']
            encoders = {}
            model = None

def get_dropdown_options():
    # Load models if not already loaded
    load_models()
    
    # Define which features should be numerical (input fields) - be very specific
    numerical_features = ['Year', 'Month']
    
    # Include all features that exist in encoders, except the specific numerical ones
    if top_10_features and encoders:
        options = {}
        for feature in top_10_features:
            # Add to dropdown options if it exists in encoders and is not in numerical_features list
            if feature in encoders and feature not in numerical_features:
                options[feature] = list(encoders[feature].classes_)
    else:
        options = {}
    
    # Add commodity category options
    options['commodity_category'] = [
        'Cereals',
        'Legumes', 
        'Vegetables',
        'Fruits',
        'Root Crops',
        'Dairy Products',
        'Meat & Poultry',
        'Fish & Seafood',
        'Spices & Herbs',
        'Other'
    ]
    
    return options

def get_web_search_answer(question):
    # Placeholder: Use SerpAPI or another web search API
    api_key = config('SERPAPI_KEY', default='')
    search_url = 'https://serpapi.com/search.json'
    params = {
        'q': question,
        'api_key': api_key,
        'engine': 'google',
        'num': 1
    }
    try:
        response = requests.get(search_url, params=params, timeout=10)
        data = response.json()
        # Try to extract the answer from the search results
        if 'answer_box' in data and 'answer' in data['answer_box']:
            return data['answer_box']['answer']
        elif 'organic_results' in data and len(data['organic_results']) > 0:
            return data['organic_results'][0].get('snippet', 'No answer found.')
        else:
            return 'No answer found.'
    except Exception as e:
        return f'Error fetching answer: {str(e)}'

def get_web_search_snippets(question, num_results=3):
    api_key = config('SERPAPI_KEY', default='')
    search_url = 'https://serpapi.com/search.json'
    params = {
        'q': question,
        'api_key': api_key,
        'engine': 'google',
        'num': num_results
    }
    try:
        response = requests.get(search_url, params=params, timeout=10)
        data = response.json()
        snippets = []
        if 'organic_results' in data:
            for result in data['organic_results'][:num_results]:
                snippet = result.get('snippet')
                if snippet:
                    snippets.append(snippet)
        return snippets
    except Exception as e:
        return []

def get_chatgpt_answer(question, web_snippets):
    client = openai.OpenAI(api_key=config('OPENAI_API_KEY', default=''))
    context = '\n'.join(web_snippets)
    prompt = (
        "You are a helpful assistant for food price and market questions in Kenya. "
        "Use the following web search results to answer the user's question as accurately and conversationally as possible. "
        "If the web results are not enough, use your own knowledge, but prefer the web context.\n"
        f"Web search results:\n{context}\n\nUser question: {question}\nAnswer:"
    )
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant for food price and market questions in Kenya."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=300,
            temperature=0.7
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        if "insufficient_quota" in str(e) or "429" in str(e):
            return "I'm currently experiencing high demand. Please try again later or contact support for assistance with your OpenAI account billing."
        return f"Error from ChatGPT: {str(e)}"

@login_required
def home(request):
    """Landing page view"""
    return render(request, 'landing.html')

@login_required
def market_trends(request):
    """Market trends view"""
    return render(request, 'predictor/market_trends.html')


def _figure_to_data_uri(fig, dpi=300):
    """Convert a Matplotlib figure to a base64 data URI for embedding in HTML."""
    buffer = io.BytesIO()
    fig.savefig(buffer, format="png", dpi=dpi, bbox_inches="tight")
    buffer.seek(0)
    image_png = buffer.getvalue()
    buffer.close()
    plt.close(fig)
    encoded = base64.b64encode(image_png).decode("utf-8")
    return f"data:image/png;base64,{encoded}"


def _run_data_analysis(df4):
    """
    Run exploratory data analysis on the uploaded dataframe.
    Returns a dict of plot data URIs keyed by plot name.
    """
    plots = {}

    # 1. Average Price per Day Name
    if {"Day Name", "Price (Ksh)"} <= set(df4.columns):
        day_avg = (
            df4.groupby("Day Name")["Price (Ksh)"]
            .mean()
            .sort_values()
        )
        fig, ax = plt.subplots(figsize=(10, 5))
        day_avg.plot(kind="bar", ax=ax)
        ax.set_title("Average Price per Day")
        ax.set_ylabel("Price (Ksh)")
        ax.set_xlabel("Day Name")
        plots["avg_price_per_day_name"] = _figure_to_data_uri(fig)

    # 2. Average Price per Month (line plot)
    if {"Month", "Price (Ksh)"} <= set(df4.columns):
        monthly_avg = df4.groupby("Month")["Price (Ksh)"].mean()
        fig, ax = plt.subplots(figsize=(10, 5), dpi=150)
        ax.plot(
            monthly_avg.index,
            monthly_avg.values,
            marker="o",
            linewidth=2.0,
            color="teal",
        )
        ax.set_title("Average Price per Month", fontsize=14, fontweight="bold")
        ax.set_xlabel("Month", fontsize=12, fontweight="bold")
        ax.set_ylabel("Average Price (Ksh)", fontsize=12, fontweight="bold")
        months_sorted = sorted(df4["Month"].unique())
        ax.set_xticks(months_sorted)
        ax.set_xticklabels(months_sorted)
        ax.grid(True)
        plots["avg_price_per_month"] = _figure_to_data_uri(fig)

    # 3. Count plots for categorical columns
    categorical_columns = [
        "Region",
        "County",
        "Market",
        "Commodity Category",
        "Commodity",
        "Priceflag",
        "Pricetype",
    ]
    available_columns = [col for col in categorical_columns if col in df4.columns]
    if available_columns:
        num_columns = 3
        num_rows = -(-len(available_columns) // num_columns)
        fig, axes = plt.subplots(num_rows, num_columns, figsize=(20, 16))
        axes = axes.ravel()

        for i, col in enumerate(available_columns):
            top_cats = df4[col].value_counts().head(10).index
            sampled_df = df4[df4[col].isin(top_cats)]
            sns.countplot(
                x=sampled_df[col],
                palette="bright",
                ax=axes[i],
                saturation=0.95,
            )
            if axes[i].containers:
                axes[i].bar_label(
                    axes[i].containers[0],
                    color="black",
                    size=10,
                    label_type="center",
                    padding=2,
                )
            axes[i].set_title(f"Count Plot of {col.capitalize()}", pad=15)
            axes[i].set_xlabel(col.capitalize())
            axes[i].set_ylabel("Count")
            axes[i].tick_params(axis="x", rotation=45)

            if col in ["Market", "Commodity"]:
                axes[i].set_xticklabels(
                    [
                        (
                            t.get_text()[:10] + "..."
                            if len(t.get_text()) > 10
                            else t.get_text()
                        )
                        for t in axes[i].get_xticklabels()
                    ]
                )
            elif col == "Commodity Category":
                axes[i].set_xticks(range(len(top_cats)))
                axes[i].set_xticklabels(top_cats, rotation=45, ha="center")

        # Remove unused subplots
        for j in range(len(available_columns), len(axes)):
            fig.delaxes(axes[j])

        fig.tight_layout()
        plots["categorical_counts"] = _figure_to_data_uri(fig)

    # 4. Total Price by Day Classification
    if {"Day_Classification", "Price (Ksh)"} <= set(df4.columns):
        total_price_per_day = df4.groupby("Day_Classification")["Price (Ksh)"].sum()
        fig, ax = plt.subplots(figsize=(8, 5), dpi=300)
        total_price_per_day.plot(kind="bar", color=["blue", "orange"], ax=ax)
        ax.set_title("Total Price by Day Classification", fontweight="bold")
        ax.set_ylabel("Total Price (Ksh)", fontweight="bold")
        ax.set_xlabel("Day Classification", fontweight="bold")
        ax.tick_params(axis="x", rotation=0)
        for p in ax.patches:
            value = p.get_height()
            ax.annotate(
                f"{value:,.2f}",
                (p.get_x() + p.get_width() / 2, value),
                ha="center",
                va="bottom",
                fontsize=10,
                fontweight="bold",
            )
        plots["total_price_by_day_classification"] = _figure_to_data_uri(fig)

    # 5. Average Price by Commodity Category Across Counties
    if {"County", "Commodity Category", "Price (Ksh)"} <= set(df4.columns):
        category_county = (
            df4.groupby(["County", "Commodity Category"])["Price (Ksh)"]
            .mean()
            .unstack()
        )
        high_price_counties = category_county.mean(axis=1) > 2000
        filtered_category_county = category_county[high_price_counties]
        if not filtered_category_county.empty:
            fig, ax = plt.subplots(figsize=(15, 6), dpi=300)
            filtered_category_county.plot(kind="bar", stacked=True, ax=ax)
            ax.set_title(
                "Average Price by Commodity Category Across Counties",
                fontweight="bold",
            )
            ax.set_ylabel("Price (Ksh)", fontweight="bold")
            ax.set_xlabel("County", fontweight="bold")
            ax.tick_params(axis="x", rotation=90, labelsize=8)
            legend = ax.legend(
                title="Commodity Category",
                bbox_to_anchor=(1.05, 1),
                loc="upper left",
            )
            legend.get_title().set_fontweight("bold")
            plots["category_county_price"] = _figure_to_data_uri(fig)

    # 6. Correlation between Price and Currency(USD) per Commodity
    if {"Commodity", "Price (Ksh)", "Currency(USD)"} <= set(df4.columns):
        currency_corr = (
            df4.groupby("Commodity")[["Price (Ksh)", "Currency(USD)"]].corr().unstack()
        )
        correlation_values = currency_corr["Currency(USD)"]["Price (Ksh)"]
        top_currency_impact = (
            correlation_values.dropna()
            .abs()
            .sort_values(ascending=False)
            .head(10)
        )
        if not top_currency_impact.empty:
            fig, ax = plt.subplots(figsize=(10, 5), dpi=300)
            sns.barplot(
                x=top_currency_impact.values,
                y=top_currency_impact.index,
                palette="coolwarm",
                ax=ax,
            )
            ax.set_title(
                "Top commodities affected by Currency Fluctuations",
                fontsize=14,
                fontweight="bold",
            )
            ax.set_xlabel(
                "Absolute Correlation with Exchange Rate",
                fontsize=12,
                fontweight="bold",
            )
            ax.set_ylabel("Commodity", fontsize=12, fontweight="bold")
            ax.grid(axis="x", linestyle="--", alpha=0.7)
            plots["currency_impact_top10"] = _figure_to_data_uri(fig)

    # 7. Top-selling commodity in the best market per region
    if {"Region", "Market", "Commodity", "Price (Ksh)"} <= set(df4.columns):
        top_selling_per_market = (
            df4.groupby(["Region", "Market", "Commodity"])["Price (Ksh)"]
            .sum()
            .reset_index()
        )
        top_market_per_region = (
            top_selling_per_market.sort_values(
                ["Region", "Price (Ksh)"], ascending=[True, False]
            )
            .groupby("Region")
            .first()
            .reset_index()
        )
        if not top_market_per_region.empty:
            fig, ax = plt.subplots(figsize=(12, 6))
            sns.barplot(
                data=top_market_per_region,
                x="Region",
                y="Price (Ksh)",
                hue="Commodity",
                dodge=False,
                palette="viridis",
                ax=ax,
            )
            for p, commodity, market in zip(
                ax.patches,
                top_market_per_region["Commodity"],
                top_market_per_region["Market"],
            ):
                ax.annotate(
                    f"{market}",
                    (
                        p.get_x() + p.get_width() / 2,
                        p.get_height() + 5000,
                    ),
                    ha="center",
                    va="bottom",
                    fontsize=11,
                    fontweight="bold",
                    color="black",
                )
                ax.annotate(
                    f"{commodity}",
                    (
                        p.get_x() + p.get_width() / 2,
                        p.get_height() / 2,
                    ),
                    ha="center",
                    va="center",
                    fontsize=10,
                    fontweight="bold",
                    color="white",
                )

            ax.set_title("Top-Selling Commodity in the Best Market Per Region")
            ax.set_xlabel("Region")
            ax.set_ylabel("Total Sales (Ksh)")
            ax.tick_params(axis="x", rotation=45)
            ax.legend(
                title="Commodity", bbox_to_anchor=(1.05, 1), loc="upper left"
            )
            plots["top_selling_per_region"] = _figure_to_data_uri(fig)

    return plots

@login_required
def contact_view(request):
    if request.method == 'POST':
        try:
            # Handle both form data and JSON data
            if request.content_type == 'application/json':
                data = json.loads(request.body.decode('utf-8'))
            else:
                data = {
                    'message': request.POST.get('message', ''),
                    'phone_number': request.POST.get('phone_number', ''),
                    'name': request.POST.get('name', ''),
                    'email': request.POST.get('email', ''),
                    'subject': request.POST.get('subject', '')
                }
            
            # Validate required fields
            if not data.get('message'):
                return JsonResponse({
                    'status': 'error',
                    'message': 'Message is required'
                }, status=400)
            
            if not data.get('phone_number'):
                return JsonResponse({
                    'status': 'error',
                    'message': 'Phone number is required'
                }, status=400)
            
            if not data.get('email'):
                return JsonResponse({
                    'status': 'error',
                    'message': 'Email is required'
                }, status=400)
            
            # Format phone number
            formatted_number = format_phone_number(data['phone_number'])
            if not formatted_number:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Invalid phone number format. Must be a valid Kenyan number.'
                }, status=400)
            
            # Prepare email message
            email_message = f"""
            Contact Form Submission

            From: {data.get('name', 'Anonymous')}
            Email: {data.get('email')}
            Phone: {formatted_number}
            Subject: {data.get('subject', 'No Subject')}

            Message:
            {data['message']}

            This message was sent from the Food Price Predictor contact form.
            """
            
            # Send email from user's email to host email
            email_sent = False
            try:
                logger.info(f"Attempting to send contact email from {data.get('email')} to {settings.EMAIL_HOST_USER}")
                if not settings.EMAIL_HOST_PASSWORD:
                    logger.error("Email password not configured")
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Email configuration error'
                    }, status=500)
                
                send_mail(
                    f'Food Price Predictor Contact: {data.get("subject", "No Subject")}',
                    email_message,
                    data.get('email'),  # From email (user's email)
                    [settings.EMAIL_HOST_USER],  # To email (host email)
                    fail_silently=False,
                )
                logger.info("Contact email sent successfully")
                email_sent = True
            except Exception as e:
                logger.error(f"Error sending contact email: {str(e)}")
                return JsonResponse({
                    'status': 'error',
                    'message': f'Error sending email: {str(e)}'
                }, status=500)
            
            # Send SMS
            sms_sent = False
            try:
                logger.info(f"Attempting to send SMS to {formatted_number}")
                sms_success, sms_message = send_sms(formatted_number, data['message'])
                
                if sms_success:
                    logger.info("SMS sent successfully")
                    sms_sent = True
                else:
                    logger.error(f"SMS sending failed: {sms_message}")
            except Exception as e:
                logger.error(f"Error sending SMS: {str(e)}")
            
            # Return appropriate response based on what was sent
            if email_sent and sms_sent:
                return JsonResponse({
                    'status': 'success',
                    'message': 'Message sent successfully via email and SMS'
                })
            elif email_sent:
                return JsonResponse({
                    'status': 'partial',
                    'message': 'Email sent successfully, but SMS failed. Please check your Twilio account settings.'
                }, status=500)
            else:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Failed to send message'
                }, status=500)
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON data: {str(e)}")
            return JsonResponse({
                'status': 'error',
                'message': 'Invalid request data format'
            }, status=400)
        except Exception as e:
            logger.error(f"Error in contact view: {str(e)}")
            return JsonResponse({
                'status': 'error',
                'message': f'Error sending message: {str(e)}'
            }, status=500)
    
    return render(request, 'predictor/contact.html')

@csrf_exempt
@require_POST
def chatbot_api(request):
    try:
        data = json.loads(request.body.decode('utf-8'))
        question = data.get('question', '')
        if not question:
            return JsonResponse({'error': 'No question provided.'}, status=400)
        web_snippets = get_web_search_snippets(question)
        answer = get_chatgpt_answer(question, web_snippets)
        return JsonResponse({'answer': answer})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def make_prediction(request):
    if request.method == 'POST':
        try:
            # Load models if not already loaded
            load_models()
            
            # Check if models loaded successfully
            if model is None:
                messages.error(request, "Prediction service is temporarily unavailable. Please try again later.")
                return render(request, 'food5.html', {
                    'form_data': request.POST,
                    'top_6_features': top_10_features or [],
                    'dropdown_options': get_dropdown_options(),
                })
            
            # Get form data
            form_data = {}
            features = []
            
            for feature in top_10_features:
                value = request.POST.get(feature)
                form_data[feature] = value
                features.append(value)

            # Encode categorical features using saved encoders
            for feature_name, encoder in encoders.items():
                if feature_name in top_10_features:
                    index = top_10_features.index(feature_name)
                    features[index] = encoder.transform([features[index]])[0]

            # Make prediction with timeout protection
            features = np.array(features).reshape(1, -1)
            log_price = model.predict(features)[0]
            actual_price = round(float(np.exp(log_price)), 2)

            # Save prediction to database
            prediction = Prediction.objects.create(
                user=request.user,
                input_data=form_data,
                prediction=actual_price
            )

            # Prepare email message with prediction details
            email_message = f"""
            Your Food Price Prediction Result

            Prediction Details:
            ------------------
            Predicted Price: KES {actual_price:.2f}

            Input Features:
            --------------
            {chr(10).join([f"{key}: {value}" for key, value in form_data.items()])}

            Thank you for using Food Price Predictor!

            Best regards,
            Food Price Predictor Team
            """

            # Send email notification (optional)
            try:
                if settings.EMAIL_HOST_USER and settings.EMAIL_HOST_PASSWORD:
                    send_mail(
                        'Your Food Price Prediction Result',
                        email_message,
                        settings.DEFAULT_FROM_EMAIL,
                        [request.user.email],
                        fail_silently=True,
                    )
                    logger.info(f"Prediction email sent successfully to {request.user.email}")
            except Exception as e:
                logger.error(f"Error sending prediction email: {str(e)}")

            # Send SMS notification if user has phone number (optional)
            try:
                if request.user.phone_number and settings.TWILIO_ACCOUNT_SID:
                    sms_message = f"Your food price prediction result: KES {actual_price:.2f}"
                    success, message = send_sms(request.user.phone_number, sms_message)
                    if success:
                        logger.info("Prediction SMS sent successfully")
                    else:
                        logger.error(f"Prediction SMS sending failed: {message}")
            except Exception as e:
                logger.error(f"Error sending SMS: {str(e)}")

            # Instead of redirecting to a result page, render the form with the prediction and previous values
            return render(request, 'food5.html', {
                'prediction': actual_price,
                'form_data': form_data,
                'top_6_features': top_10_features,
                'dropdown_options': {feature: list(encoders[feature].classes_) for feature in top_10_features if feature in encoders},
            })

        except Exception as e:
            logger.error(f"Error making prediction: {str(e)}")
            logger.error(f"Error type: {type(e).__name__}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            messages.error(request, "An error occurred while making the prediction. Please try again.")
            return render(request, 'food5.html', {
                'form_data': request.POST,
                'top_6_features': top_10_features,
                'dropdown_options': {feature: list(encoders[feature].classes_) for feature in top_10_features if feature in encoders},
            })
    # GET request
    load_models()  # Ensure models are loaded
    return render(request, 'food5.html', {
        'top_6_features': top_10_features or [],
        'dropdown_options': get_dropdown_options(),
    })

@login_required
def download_predictions(request):
    # Get predictions for the current user
    predictions = Prediction.objects.filter(user=request.user)

    # Prepare CSV
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    
    # Write header
    headers = list(predictions.first().input_data.keys()) + ['prediction', 'timestamp (EAT)']
    writer.writerow(headers)

    # Write data
    eat = pytz.timezone('Africa/Nairobi')
    for prediction in predictions:
        # Convert timestamp to EAT
        eat_time = timezone.localtime(prediction.timestamp, eat)
        row = list(prediction.input_data.values()) + [prediction.prediction, eat_time.strftime('%Y-%m-%d %H:%M:%S')]
        writer.writerow(row)

    buffer.seek(0)
    response = HttpResponse(buffer, content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="predictions.csv"'
    return response

@login_required
def notify_user(request):
    send_sms('+254742423200', 'Hello from Django + Twilio!')
    return HttpResponse("SMS sent!")

@login_required
def test_twilio(request):
    """Test endpoint to verify Twilio configuration"""
    try:
        # Log request details
        logger.info(f"Test Twilio request received from user: {request.user.username}")
        logger.info(f"User phone number: {request.user.phone_number}")

        # Log configuration (safely)
        logger.info("Testing Twilio configuration...")
        logger.info(f"Account SID configured: {bool(settings.TWILIO_ACCOUNT_SID)}")
        logger.info(f"Auth Token configured: {bool(settings.TWILIO_AUTH_TOKEN)}")
        logger.info(f"Phone Number configured: {bool(settings.TWILIO_PHONE_NUMBER)}")

        if not request.user.phone_number:
            return HttpResponse("Error: User has no phone number configured", status=400)

        # Test client initialization
        try:
            client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
            logger.info("Twilio client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Twilio client: {str(e)}")
            return HttpResponse(f"Error initializing Twilio client: {str(e)}", status=500)
        
        # Test sending message
        try:
            message = client.messages.create(
                body="This is a test message from Food Price Predictor",
                from_=settings.TWILIO_PHONE_NUMBER,
                to=request.user.phone_number
            )
            logger.info(f"Test message sent successfully. SID: {message.sid}")
            return HttpResponse(f"Test message sent successfully! SID: {message.sid}")
        except Exception as e:
            logger.error(f"Failed to send test message: {str(e)}")
            return HttpResponse(f"Error sending test message: {str(e)}", status=500)
            
    except Exception as e:
        logger.error(f"Unexpected error in test_twilio: {str(e)}")
        logger.error(f"Error type: {type(e).__name__}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return HttpResponse(f"Unexpected error: {str(e)}", status=500)

@login_required
def cheapest_market(request):
    dropdown_options = get_dropdown_options()
    cheapest_market = None
    searched = False
    if request.method == 'POST':
        # Use actual feature names from top_10_features
        commodity = request.POST.get('Commodity')
        region = request.POST.get('Region')
        # Query CommunityReport for real user-submitted prices
        reports = CommunityReport.objects.filter(food_item=commodity, region=region)
        if reports.exists():
            best_report = reports.order_by('price').first()
            cheapest_market = {
                'market': best_report.market,
                'region': best_report.region,
                'food_item': best_report.food_item,
                'price': best_report.price
            }
        searched = True
    return render(request, 'predictor/cheapest_market.html', {
        'cheapest_market': cheapest_market,
        'searched': searched,
        'top_10_features': top_10_features,
        'dropdown_options': dropdown_options
    })

@login_required
def alerts(request):
    dropdown_options = get_dropdown_options()
    if 'subscriptions' not in request.session:
        request.session['subscriptions'] = []
    subscriptions = request.session['subscriptions']
    subscribed = False
    sub_commodity = None
    sub_region = None
    if request.method == 'POST':
        commodity = request.POST.get('Commodity')
        region = request.POST.get('Region')
        if commodity and region:
            new_sub = {'Commodity': commodity, 'Region': region}
            if new_sub not in subscriptions:
                subscriptions.append(new_sub)
                request.session['subscriptions'] = subscriptions
            subscribed = True
            sub_commodity = commodity
            sub_region = region
    return render(request, 'predictor/alerts.html', {
        'subscribed': subscribed,
        'sub_commodity': sub_commodity,
        'sub_region': sub_region,
        'subscriptions': subscriptions,
        'top_10_features': top_10_features,
        'dropdown_options': dropdown_options
    })

@login_required
def community_reporting(request):
    dropdown_options = get_dropdown_options()
    submitted = False
    if request.method == 'POST':
        commodity = request.POST.get('Commodity')
        commodity_category = request.POST.get('commodity_category')
        county = request.POST.get('County')
        region = request.POST.get('Region')
        market = request.POST.get('Market')
        price = request.POST.get('price')
        unit_quantity = request.POST.get('unit_quantity', '1 kg')
        if commodity and region and market and price:
            CommunityReport.objects.create(
                user=request.user,
                food_item=commodity,
                commodity_category=commodity_category,
                county=county,
                region=region,
                market=market,
                price=float(price),
                unit_quantity=unit_quantity
            )
            submitted = True
    reports = CommunityReport.objects.all()[:50]  # Show recent 50
    return render(request, 'predictor/community_reporting.html', {
        'submitted': submitted,
        'reports': reports,
        'top_10_features': top_10_features,
        'dropdown_options': dropdown_options
    })

@login_required
def budget_estimator(request):
    dropdown_options = get_dropdown_options()
    budget = None
    if request.method == 'POST':
        try:
            income = float(request.POST.get('income'))
            household_size = int(request.POST.get('household_size'))
            # Demo rule: 40% of income for food
            total_budget = 0.4 * income
            maize = 0.5 * total_budget
            rice = 0.3 * total_budget
            beans = 0.2 * total_budget
            percent_of_income = int((total_budget / income) * 100)
            budget = {
                'total': total_budget,
                'maize': maize,
                'rice': rice,
                'beans': beans,
                'percent_of_income': percent_of_income,
                'household_size': household_size
            }
        except Exception:
            budget = None
    return render(request, 'predictor/budget_estimator.html', {
        'budget': budget,
        'top_10_features': top_10_features,
        'dropdown_options': dropdown_options
    })

@login_required
def nutrition_tips(request):
    dropdown_options = get_dropdown_options()
    tip = None
    tips = {
        'Bananas': 'Bananas are rich in potassium and good for energy.',
        'Beans': 'Beans are rich in protein and fiber. Add some grains or starchy foods for a complete diet.',
        'Maize': 'Maize is a good source of carbohydrates. Pair it with beans or vegetables for a balanced meal.',
        'Rice': 'Rice provides energy, but combine it with legumes and greens for more protein and vitamins.'
    }
    if request.method == 'POST':
        main_staple = request.POST.get('Commodity')
        if main_staple in tips:
            tip = tips[main_staple]
    return render(request, 'predictor/nutrition_tips.html', {
        'tip': tip,
        'top_10_features': top_10_features,
        'dropdown_options': dropdown_options
    })

@login_required
def planting_selling_suggestions(request):
    dropdown_options = get_dropdown_options()
    suggestion = None
    planting_seasons = {
        'March': 'Ideal for planting maize in most regions due to long rains.',
        'April': 'Continue planting maize and beans; ensure soil moisture is adequate.',
        'May': 'Weeding and top-dressing for maize; monitor for pests.',
        'June': 'Prepare for harvesting early-planted crops; sell surplus at local markets.',
        'October': 'Short rains season; plant fast-maturing crops like beans.',
        'November': 'Continue with short rains planting; focus on vegetables and beans.'
    }
    if request.method == 'POST':
        region = request.POST.get('Region')
        month = request.POST.get('month')
        if month in planting_seasons:
            suggestion = f"{planting_seasons[month]} (Region: {region})"
        else:
            suggestion = f"No specific planting/selling advice for {month}. Consult your local extension officer for more info. (Region: {region})"
    return render(request, 'predictor/planting_selling_suggestions.html', {
        'suggestion': suggestion,
        'top_10_features': top_10_features,
        'dropdown_options': dropdown_options
    })

@login_required
def impact_dashboard(request):
    return render(request, 'predictor/impact_dashboard.html')


@login_required
def data_analysis(request):
    """
    View to upload a dataset and display key exploratory data analysis plots.
    """
    plots = {}
    df_columns = []
    error_message = None

    # Per-user cached dataset path
    cache_dir = os.path.join(settings.MEDIA_ROOT, "data_analysis")
    os.makedirs(cache_dir, exist_ok=True)
    cache_path = os.path.join(cache_dir, f"user_{request.user.id}.csv")

    if request.method == "POST" and request.FILES.get("dataset"):
        uploaded_file = request.FILES["dataset"]
        try:
            # Save uploaded file to per-user cache location
            with open(cache_path, "wb+") as destination:
                for chunk in uploaded_file.chunks():
                    destination.write(chunk)

            # Attempt to read as CSV from cached file.
            df4 = pd.read_csv(cache_path)
            df_columns = list(df4.columns)
            plots = _run_data_analysis(df4)
            if not plots:
                error_message = (
                    "Dataset loaded, but required columns were not found for the "
                    "predefined analyses. Please ensure your file has matching column names."
                )
        except Exception as e:
            error_message = f"Error processing dataset: {str(e)}"
    elif request.method == "POST":
        # No new file provided; fall back to cached dataset if available
        if os.path.exists(cache_path):
            try:
                df4 = pd.read_csv(cache_path)
                df_columns = list(df4.columns)
                plots = _run_data_analysis(df4)
                if not plots:
                    error_message = (
                        "Cached dataset loaded, but required columns were not found for the "
                        "predefined analyses. Please ensure your file has matching column names."
                    )
            except Exception as e:
                error_message = f"Error processing cached dataset: {str(e)}"
        else:
            error_message = "Please select a CSV file to upload."
    else:
        # GET request: if a cached dataset exists, load and analyze it automatically
        if os.path.exists(cache_path):
            try:
                df4 = pd.read_csv(cache_path)
                df_columns = list(df4.columns)
                plots = _run_data_analysis(df4)
            except Exception:
                # Fail silently here; user can re-upload
                pass

    context = {
        "plots": plots,
        "df_columns": df_columns,
        "error_message": error_message,
    }
    return render(request, "predictor/data_analysis.html", context)

@require_POST
def set_language(request):
    lang = request.POST.get('language', 'en')
    request.session['lang'] = lang
    next_url = request.META.get('HTTP_REFERER', reverse('home'))
    return redirect(next_url)

def get_lang(request):
    return request.session.get('lang', 'en')

@csrf_exempt
def market_data_api(request):
    """API endpoint to serve market data with coordinates for the interactive map"""
    try:
        # Get recent community reports (last 7 days)
        from django.utils import timezone
        from datetime import timedelta
        
        recent_date = timezone.now() - timedelta(days=7)
        reports = CommunityReport.objects.filter(timestamp__gte=recent_date)
        
        # Group reports by market and get latest prices
        market_data = {}
        for report in reports:
            market_key = f"{report.market}_{report.region}"
            if market_key not in market_data:
                market_data[market_key] = {
                    'market': report.market,
                    'region': report.region,
                    'county': report.county or 'Unknown',
                    'commodities': {},
                    'last_updated': report.timestamp
                }
            
            # Store latest price for each commodity
            if report.food_item not in market_data[market_key]['commodities']:
                market_data[market_key]['commodities'][report.food_item] = {
                    'price': report.price,
                    'category': report.commodity_category or 'Other',
                    'timestamp': report.timestamp
                }
        
        # Add coordinates for major Kenyan markets
        market_coordinates = {
            'Nairobi_Central': {'lat': -1.2921, 'lng': 36.8219},
            'Mombasa_Coast': {'lat': -4.0435, 'lng': 39.6682},
            'Kisumu_Western': {'lat': -0.0917, 'lng': 34.7680},
            'Nakuru_Rift Valley': {'lat': -0.3072, 'lng': 36.0800},
            'Eldoret_Rift Valley': {'lat': 0.5143, 'lng': 35.2698},
            'Thika_Central': {'lat': -1.0333, 'lng': 37.0833},
            'Meru_Eastern': {'lat': 0.0500, 'lng': 37.6500},
            'Kakamega_Western': {'lat': 0.2833, 'lng': 34.7500},
            'Nyeri_Central': {'lat': -0.4167, 'lng': 36.9500},
            'Garissa_North Eastern': {'lat': -0.4569, 'lng': 39.6583},
            'Machakos_Eastern': {'lat': -1.5167, 'lng': 37.2667},
            'Kitui_Eastern': {'lat': -1.3667, 'lng': 38.0167},
            'Embu_Eastern': {'lat': -0.5333, 'lng': 37.4500},
            'Kericho_Rift Valley': {'lat': -0.3667, 'lng': 35.2833},
            'Kitale_Rift Valley': {'lat': 1.0167, 'lng': 35.0000},
            'Malindi_Coast': {'lat': -3.2167, 'lng': 40.1167},
            'Lamu_Coast': {'lat': -2.2667, 'lng': 40.9000},
            'Isiolo_Eastern': {'lat': 0.3500, 'lng': 37.5833},
            'Marsabit_Eastern': {'lat': 2.3333, 'lng': 37.9833},
            'Wajir_North Eastern': {'lat': 1.7500, 'lng': 40.0667}
        }
        
        # Prepare response data
        response_data = []
        for market_key, data in market_data.items():
            # Try to find coordinates for this market
            coordinates = None
            for coord_key, coords in market_coordinates.items():
                if (data['market'].lower() in coord_key.lower() or 
                    data['region'].lower() in coord_key.lower()):
                    coordinates = coords
                    break
            
            # If no exact match, use region-based coordinates
            if not coordinates:
                region_coords = {
                    'Nairobi': {'lat': -1.2921, 'lng': 36.8219},
                    'Mombasa': {'lat': -4.0435, 'lng': 39.6682},
                    'Kisumu': {'lat': -0.0917, 'lng': 34.7680},
                    'Nakuru': {'lat': -0.3072, 'lng': 36.0800},
                    'Eldoret': {'lat': 0.5143, 'lng': 35.2698},
                    'Central': {'lat': -0.4167, 'lng': 36.9500},
                    'Eastern': {'lat': -0.5333, 'lng': 37.4500},
                    'Western': {'lat': 0.2833, 'lng': 34.7500},
                    'Coast': {'lat': -4.0435, 'lng': 39.6682},
                    'Rift Valley': {'lat': -0.3072, 'lng': 36.0800},
                    'North Eastern': {'lat': 1.7500, 'lng': 40.0667}
                }
                coordinates = region_coords.get(data['region'], {'lat': -0.0236, 'lng': 37.9062})  # Default to Kenya center
            
            response_data.append({
                'id': market_key,
                'name': data['market'],
                'region': data['region'],
                'county': data['county'],
                'coordinates': coordinates,
                'commodities': data['commodities'],
                'last_updated': data['last_updated'].isoformat(),
                'commodity_count': len(data['commodities'])
            })
        
        return JsonResponse({
            'status': 'success',
            'data': response_data,
            'total_markets': len(response_data)
        })
        
    except Exception as e:
        logger.error(f"Error in market_data_api: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)

@staff_member_required
def download_community_reports(request):
    reports = CommunityReport.objects.all().order_by('-timestamp')
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="community_reports.csv"'
    writer = csv.writer(response)
    writer.writerow(['Food Item', 'Category', 'County', 'Region', 'Market', 'Price (KES)', 'Unit Quantity', 'Submitted By', 'Timestamp (EAT)'])
    eat = pytz.timezone('Africa/Nairobi')
    for r in reports:
        # Convert timestamp to EAT
        eat_time = timezone.localtime(r.timestamp, eat)
        writer.writerow([
            r.food_item,
            r.commodity_category or 'N/A',
            r.county or 'N/A',
            r.region,
            r.market,
            f"{r.price:.2f}",
            r.unit_quantity or '1 kg',
            r.user.username,
            eat_time.strftime('%Y-%m-%d %H:%M:%S')
        ])
    return response
