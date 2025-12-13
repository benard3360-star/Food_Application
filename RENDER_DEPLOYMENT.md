# Render Deployment Guide

This guide will help you deploy your Food Price Predictor application to Render.

## Prerequisites

1. A Render account (sign up at https://render.com)
2. Your code pushed to GitHub repository
3. Environment variables configured

## Deployment Steps

### 1. Push to GitHub

First, make sure your code is pushed to your GitHub repository:

```bash
git add .
git commit -m "Add Render deployment configuration"
git push origin main
```

### 2. Create Render Services

#### Option A: Using render.yaml (Recommended)
1. Go to https://dashboard.render.com
2. Click "New" → "Blueprint"
3. Connect your GitHub repository
4. Render will automatically detect the `render.yaml` file
5. Review the services and click "Apply"

#### Option B: Manual Setup
1. **Create PostgreSQL Database:**
   - Go to Render Dashboard
   - Click "New" → "PostgreSQL"
   - Name: `food-price-predictor-db`
   - Plan: Free
   - Click "Create Database"
   - Note down the database connection details

2. **Create Web Service:**
   - Click "New" → "Web Service"
   - Connect your GitHub repository
   - Configure:
     - Name: `food-price-predictor`
     - Environment: `Python 3`
     - Build Command: `./build.sh`
     - Start Command: `gunicorn food_price_project.wsgi:application`

### 3. Configure Environment Variables

In your Render web service settings, add these environment variables:

#### Required Variables:
```
DJANGO_SETTINGS_MODULE=food_price_project.settings_prod
SECRET_KEY=<generate-a-secure-secret-key>
DEBUG=False
ALLOWED_HOSTS=<your-app-name>.onrender.com
DATABASE_URL=<provided-by-render-postgresql-service>
```

#### Optional Variables (for full functionality):
```
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
TWILIO_ACCOUNT_SID=your_twilio_account_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_PHONE_NUMBER=your_twilio_phone_number
OPENAI_API_KEY=your_openai_api_key
```

### 4. Deploy

1. Click "Create Web Service" or "Deploy Latest Commit"
2. Wait for the build to complete (5-10 minutes)
3. Your app will be available at `https://<your-app-name>.onrender.com`

## Important Notes

### Database Connection
- Render automatically provides `DATABASE_URL` for PostgreSQL services
- The app will use this URL automatically in production

### Static Files
- Static files are handled by WhiteNoise
- No additional configuration needed

### Build Process
The `build.sh` script will:
1. Install Python dependencies
2. Collect static files
3. Run database migrations

### Free Tier Limitations
- Services sleep after 15 minutes of inactivity
- First request after sleep may take 30+ seconds
- 750 hours/month limit

## Troubleshooting

### Build Failures
1. Check build logs in Render dashboard
2. Ensure all dependencies are in `requirements.txt`
3. Verify `build.sh` has execute permissions

### Runtime Errors
1. Check application logs in Render dashboard
2. Verify environment variables are set correctly
3. Check database connection

### Static Files Not Loading
1. Ensure `STATIC_ROOT` is set correctly
2. Check if `collectstatic` ran successfully
3. Verify WhiteNoise middleware is configured

## Post-Deployment

1. **Create Superuser:**
   ```bash
   # In Render shell (if available) or via Django admin
   python manage.py createsuperuser
   ```

2. **Test Application:**
   - Visit your app URL
   - Test user registration/login
   - Test price prediction functionality

3. **Monitor:**
   - Check logs regularly
   - Monitor performance
   - Set up alerts if needed

## Custom Domain (Optional)

1. Go to your web service settings
2. Add your custom domain
3. Configure DNS records as instructed
4. Update `ALLOWED_HOSTS` environment variable

## Support

- Render Documentation: https://render.com/docs
- Django Deployment Guide: https://docs.djangoproject.com/en/stable/howto/deployment/

Your Food Price Predictor app should now be live on Render!