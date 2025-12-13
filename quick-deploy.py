#!/usr/bin/env python
"""
Quick deployment script for Food Price Predictor
This script will guide you through the deployment process
"""

import os
import sys
import subprocess

def print_banner():
    print("🚀 Food Price Predictor - Quick Deploy")
    print("=" * 50)

def check_requirements():
    """Check if all required files exist"""
    required_files = [
        'manage.py',
        'requirements-prod.txt',
        'food_price_project/settings_prod.py',
        'Procfile'
    ]
    
    missing_files = []
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    if missing_files:
        print("❌ Missing required files:")
        for file in missing_files:
            print(f"   - {file}")
        return False
    
    print("✅ All required files found")
    return True

def get_user_input():
    """Get deployment preferences from user"""
    print("\n📋 Deployment Configuration")
    print("-" * 30)
    
    # Platform choice
    print("\nChoose your deployment platform:")
    print("1. Railway (Recommended - Easiest)")
    print("2. Render (Good free tier)")
    print("3. Heroku (Professional)")
    print("4. DigitalOcean (Performance)")
    
    while True:
        choice = input("\nEnter your choice (1-4): ").strip()
        if choice in ['1', '2', '3', '4']:
            platforms = {
                '1': 'Railway',
                '2': 'Render', 
                '3': 'Heroku',
                '4': 'DigitalOcean'
            }
            platform = platforms[choice]
            break
        print("Please enter a valid choice (1-4)")
    
    # Environment variables
    print(f"\n🔧 Setting up environment variables for {platform}...")
    print("You'll need to provide these values:")
    
    env_vars = {}
    env_vars['SECRET_KEY'] = input("Django Secret Key (generate at https://djecrety.ir/): ").strip()
    env_vars['EMAIL_HOST_USER'] = input("Gmail address: ").strip()
    env_vars['EMAIL_HOST_PASSWORD'] = input("Gmail App Password: ").strip()
    env_vars['TWILIO_ACCOUNT_SID'] = input("Twilio Account SID: ").strip()
    env_vars['TWILIO_AUTH_TOKEN'] = input("Twilio Auth Token: ").strip()
    env_vars['TWILIO_PHONE_NUMBER'] = input("Twilio Phone Number: ").strip()
    env_vars['OPENAI_API_KEY'] = input("OpenAI API Key: ").strip()
    
    return platform, env_vars

def generate_deployment_commands(platform, env_vars):
    """Generate platform-specific deployment commands"""
    
    commands = {
        'Railway': f"""
# Railway Deployment Commands
# 1. Sign up at https://railway.app
# 2. Connect your GitHub repository
# 3. Add PostgreSQL database
# 4. Set these environment variables:

railway variables set DJANGO_SETTINGS_MODULE=food_price_project.settings_prod
railway variables set SECRET_KEY={env_vars['SECRET_KEY']}
railway variables set EMAIL_HOST_USER={env_vars['EMAIL_HOST_USER']}
railway variables set EMAIL_HOST_PASSWORD={env_vars['EMAIL_HOST_PASSWORD']}
railway variables set TWILIO_ACCOUNT_SID={env_vars['TWILIO_ACCOUNT_SID']}
railway variables set TWILIO_AUTH_TOKEN={env_vars['TWILIO_AUTH_TOKEN']}
railway variables set TWILIO_PHONE_NUMBER={env_vars['TWILIO_PHONE_NUMBER']}
railway variables set OPENAI_API_KEY={env_vars['OPENAI_API_KEY']}
""",
        
        'Render': f"""
# Render Deployment Commands
# 1. Sign up at https://render.com
# 2. Create Web Service from GitHub
# 3. Add PostgreSQL database
# 4. Set these environment variables in Render dashboard:

DJANGO_SETTINGS_MODULE=food_price_project.settings_prod
SECRET_KEY={env_vars['SECRET_KEY']}
EMAIL_HOST_USER={env_vars['EMAIL_HOST_USER']}
EMAIL_HOST_PASSWORD={env_vars['EMAIL_HOST_PASSWORD']}
TWILIO_ACCOUNT_SID={env_vars['TWILIO_ACCOUNT_SID']}
TWILIO_AUTH_TOKEN={env_vars['TWILIO_AUTH_TOKEN']}
TWILIO_PHONE_NUMBER={env_vars['TWILIO_PHONE_NUMBER']}
OPENAI_API_KEY={env_vars['OPENAI_API_KEY']}
""",
        
        'Heroku': f"""
# Heroku Deployment Commands
# 1. Install Heroku CLI and login
# 2. Create app: heroku create your-app-name
# 3. Add database: heroku addons:create heroku-postgresql:hobby-dev
# 4. Set environment variables:

heroku config:set DJANGO_SETTINGS_MODULE=food_price_project.settings_prod
heroku config:set SECRET_KEY={env_vars['SECRET_KEY']}
heroku config:set EMAIL_HOST_USER={env_vars['EMAIL_HOST_USER']}
heroku config:set EMAIL_HOST_PASSWORD={env_vars['EMAIL_HOST_PASSWORD']}
heroku config:set TWILIO_ACCOUNT_SID={env_vars['TWILIO_ACCOUNT_SID']}
heroku config:set TWILIO_AUTH_TOKEN={env_vars['TWILIO_AUTH_TOKEN']}
heroku config:set TWILIO_PHONE_NUMBER={env_vars['TWILIO_PHONE_NUMBER']}
heroku config:set OPENAI_API_KEY={env_vars['OPENAI_API_KEY']}

# 5. Deploy:
git push heroku main
heroku run python manage.py migrate
heroku run python manage.py createsuperuser
""",
        
        'DigitalOcean': f"""
# DigitalOcean App Platform Deployment
# 1. Sign up at https://cloud.digitalocean.com
# 2. Create App from GitHub
# 3. Add PostgreSQL database
# 4. Set these environment variables in App Spec:

DJANGO_SETTINGS_MODULE=food_price_project.settings_prod
SECRET_KEY={env_vars['SECRET_KEY']}
EMAIL_HOST_USER={env_vars['EMAIL_HOST_USER']}
EMAIL_HOST_PASSWORD={env_vars['EMAIL_HOST_PASSWORD']}
TWILIO_ACCOUNT_SID={env_vars['TWILIO_ACCOUNT_SID']}
TWILIO_AUTH_TOKEN={env_vars['TWILIO_AUTH_TOKEN']}
TWILIO_PHONE_NUMBER={env_vars['TWILIO_PHONE_NUMBER']}
OPENAI_API_KEY={env_vars['OPENAI_API_KEY']}
"""
    }
    
    return commands[platform]

def main():
    print_banner()
    
    # Check requirements
    if not check_requirements():
        print("\n❌ Please ensure all required files are present before deploying.")
        sys.exit(1)
    
    # Get user input
    platform, env_vars = get_user_input()
    
    # Generate commands
    commands = generate_deployment_commands(platform, env_vars)
    
    # Save commands to file
    with open(f'{platform.lower()}-deploy-commands.txt', 'w') as f:
        f.write(commands)
    
    print(f"\n✅ Deployment commands saved to {platform.lower()}-deploy-commands.txt")
    print(f"\n🚀 Ready to deploy to {platform}!")
    print("\n📋 Next steps:")
    print("1. Push your code to GitHub")
    print("2. Follow the commands in the generated file")
    print("3. Test your deployed application")
    
    print(f"\n📖 For detailed instructions, see DEPLOYMENT.md")

if __name__ == "__main__":
    main()
