#!/usr/bin/env python
"""
Deployment script for Food Price Predictor
Run this script to prepare your app for deployment
"""

import os
import subprocess
import sys

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"\n🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e.stderr}")
        return None

def main():
    print("🚀 Food Price Predictor Deployment Preparation")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not os.path.exists('manage.py'):
        print("❌ Error: manage.py not found. Please run this script from the project root directory.")
        sys.exit(1)
    
    # Collect static files
    run_command("python manage.py collectstatic --noinput", "Collecting static files")
    
    # Run migrations
    run_command("python manage.py makemigrations", "Creating migrations")
    run_command("python manage.py migrate", "Running migrations")
    
    # Create superuser (optional)
    print("\n👤 Do you want to create a superuser? (y/n): ", end="")
    if input().lower() == 'y':
        run_command("python manage.py createsuperuser", "Creating superuser")
    
    print("\n✅ Deployment preparation completed!")
    print("\n📋 Next steps:")
    print("1. Set up your environment variables")
    print("2. Choose a deployment platform")
    print("3. Deploy your application")
    print("\n📖 See deployment instructions in DEPLOYMENT.md")

if __name__ == "__main__":
    main()
