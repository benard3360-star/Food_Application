# 🚀 Food Price Predictor - Deployment Guide

This guide will help you deploy your Django food price prediction app to various cloud platforms.

## 📋 Prerequisites

1. **GitHub Repository**: Push your code to GitHub
2. **API Keys**: Get your API keys ready:
   - Twilio (for SMS)
   - OpenAI (for chatbot)
   - Gmail App Password (for email)

## 🔧 Pre-Deployment Setup

### 1. Environment Variables
Copy `env.example` to `.env` and fill in your values:

```bash
cp env.example .env
```

Required environment variables:
- `SECRET_KEY`: Django secret key
- `EMAIL_HOST_USER`: Your Gmail address
- `EMAIL_HOST_PASSWORD`: Gmail app password
- `TWILIO_ACCOUNT_SID`: Twilio account SID
- `TWILIO_AUTH_TOKEN`: Twilio auth token
- `TWILIO_PHONE_NUMBER`: Your Twilio phone number
- `OPENAI_API_KEY`: OpenAI API key

### 2. Prepare for Deployment
Run the deployment preparation script:

```bash
python deploy.py
```

## 🌐 Deployment Options

### Option 1: Railway (Recommended)

**Why Railway?**
- ✅ Free tier available
- ✅ Automatic HTTPS
- ✅ Built-in PostgreSQL
- ✅ Easy environment variables
- ✅ Automatic deployments

**Steps:**

1. **Sign up** at [railway.app](https://railway.app)

2. **Connect GitHub**:
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose your repository

3. **Add Database**:
   - Click "New" → "Database" → "PostgreSQL"
   - Railway will automatically set `DATABASE_URL`

4. **Set Environment Variables**:
   ```
   DJANGO_SETTINGS_MODULE=food_price_project.settings_prod
   SECRET_KEY=your-secret-key
   EMAIL_HOST_USER=your-email@gmail.com
   EMAIL_HOST_PASSWORD=your-app-password
   TWILIO_ACCOUNT_SID=your-twilio-sid
   TWILIO_AUTH_TOKEN=your-twilio-token
   TWILIO_PHONE_NUMBER=your-twilio-number
   OPENAI_API_KEY=your-openai-key
   ```

5. **Deploy**:
   - Railway will automatically deploy
   - Your app will be available at `https://your-app-name.railway.app`

### Option 2: Render

**Why Render?**
- ✅ Free tier available
- ✅ Automatic deployments
- ✅ Built-in PostgreSQL
- ✅ Good performance

**Steps:**

1. **Sign up** at [render.com](https://render.com)

2. **Create Web Service**:
   - Connect your GitHub repository
   - Choose "Web Service"

3. **Configure**:
   ```
   Build Command: pip install -r requirements-prod.txt
   Start Command: gunicorn food_price_project.wsgi:application
   ```

4. **Add Database**:
   - Create a PostgreSQL database
   - Copy the database URL

5. **Set Environment Variables**:
   ```
   DJANGO_SETTINGS_MODULE=food_price_project.settings_prod
   DATABASE_URL=your-database-url
   SECRET_KEY=your-secret-key
   EMAIL_HOST_USER=your-email@gmail.com
   EMAIL_HOST_PASSWORD=your-app-password
   TWILIO_ACCOUNT_SID=your-twilio-sid
   TWILIO_AUTH_TOKEN=your-twilio-token
   TWILIO_PHONE_NUMBER=your-twilio-number
   OPENAI_API_KEY=your-openai-key
   ```

### Option 3: Heroku

**Steps:**

1. **Install Heroku CLI** and login

2. **Create Heroku App**:
   ```bash
   heroku create your-app-name
   ```

3. **Add PostgreSQL**:
   ```bash
   heroku addons:create heroku-postgresql:hobby-dev
   ```

4. **Set Environment Variables**:
   ```bash
   heroku config:set DJANGO_SETTINGS_MODULE=food_price_project.settings_prod
   heroku config:set SECRET_KEY=your-secret-key
   heroku config:set EMAIL_HOST_USER=your-email@gmail.com
   heroku config:set EMAIL_HOST_PASSWORD=your-app-password
   heroku config:set TWILIO_ACCOUNT_SID=your-twilio-sid
   heroku config:set TWILIO_AUTH_TOKEN=your-twilio-token
   heroku config:set TWILIO_PHONE_NUMBER=your-twilio-number
   heroku config:set OPENAI_API_KEY=your-openai-key
   ```

5. **Deploy**:
   ```bash
   git push heroku main
   heroku run python manage.py migrate
   heroku run python manage.py createsuperuser
   ```

## 🔐 Getting API Keys

### Gmail App Password
1. Enable 2-factor authentication on Gmail
2. Go to Google Account settings
3. Security → App passwords
4. Generate a new app password
5. Use this password in `EMAIL_HOST_PASSWORD`

### Twilio
1. Sign up at [twilio.com](https://twilio.com)
2. Get your Account SID and Auth Token from the dashboard
3. Buy a phone number for SMS

### OpenAI
1. Sign up at [openai.com](https://openai.com)
2. Go to API keys section
3. Create a new API key

## 🐳 Docker Deployment (Alternative)

If you prefer Docker:

```bash
# Build the image
docker build -t food-price-predictor .

# Run with environment variables
docker run -d \
  -p 8000:8000 \
  -e SECRET_KEY=your-secret-key \
  -e EMAIL_HOST_USER=your-email@gmail.com \
  -e EMAIL_HOST_PASSWORD=your-app-password \
  -e TWILIO_ACCOUNT_SID=your-twilio-sid \
  -e TWILIO_AUTH_TOKEN=your-twilio-token \
  -e TWILIO_PHONE_NUMBER=your-twilio-number \
  -e OPENAI_API_KEY=your-openai-key \
  food-price-predictor
```

## 🚨 Troubleshooting

### Common Issues:

1. **Static files not loading**:
   - Ensure `STATIC_ROOT` is set correctly
   - Run `python manage.py collectstatic`

2. **Database connection errors**:
   - Check your database URL
   - Ensure PostgreSQL is running

3. **Email not sending**:
   - Verify Gmail app password
   - Check email settings

4. **SMS not working**:
   - Verify Twilio credentials
   - Check phone number format

### Debug Mode:
To enable debug mode temporarily, set:
```
DEBUG=True
```

## 📊 Monitoring

After deployment, monitor your app:
- Check logs regularly
- Monitor API usage (Twilio, OpenAI)
- Set up error tracking (Sentry)

## 🔄 Updates

To update your deployed app:
1. Push changes to GitHub
2. Platform will automatically redeploy
3. Run migrations if needed: `python manage.py migrate`

## 💰 Cost Estimation

- **Railway**: Free tier → $5/month
- **Render**: Free tier → $7/month  
- **Heroku**: $7/month minimum
- **DigitalOcean**: $5/month minimum

## 🎉 Success!

Once deployed, your app will be available at your platform's URL. Test all features:
- User registration/login
- Price predictions
- Email notifications
- SMS notifications
- Chatbot functionality

---

**Need help?** Check the platform's documentation or create an issue in your repository.
