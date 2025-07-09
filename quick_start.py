#!/usr/bin/env python3
"""
Finance Bot Quick Start Script

This script helps you quickly set up and test the finance bot.
It will guide you through configuration and run basic tests.
"""

import os
import sys
import subprocess
from pathlib import Path

def print_header(title):
    """Print a formatted header"""
    print(f"\n{'='*60}")
    print(f"🚀 {title}")
    print(f"{'='*60}")

def print_step(step_num, title):
    """Print a formatted step header"""
    print(f"\n📋 Step {step_num}: {title}")
    print("-" * 40)

def check_python_version():
    """Check if Python version is compatible"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python 3.8 or higher is required")
        print(f"   Current version: {version.major}.{version.minor}.{version.micro}")
        return False
    else:
        print(f"✅ Python version: {version.major}.{version.minor}.{version.micro}")
        return True

def install_dependencies():
    """Install required dependencies"""
    print("📦 Installing dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Dependencies installed successfully!")
        return True
    except subprocess.CalledProcessError:
        print("❌ Failed to install dependencies")
        print("   Try running: pip install -r requirements.txt")
        return False

def setup_environment():
    """Set up environment configuration"""
    env_file = Path(".env")
    env_example = Path(".env.example")
    
    if env_file.exists():
        print("✅ .env file already exists")
        return True
    
    if env_example.exists():
        try:
            # Copy example to .env
            content = env_example.read_text()
            env_file.write_text(content)
            print("✅ Created .env file from template")
            print("📝 Please edit .env file with your API keys and phone numbers")
            return True
        except Exception as e:
            print(f"❌ Error creating .env file: {e}")
            return False
    else:
        print("❌ .env.example file not found")
        return False

def test_basic_functionality():
    """Test basic bot functionality"""
    print("🧪 Testing basic functionality...")
    
    try:
        # Test data fetching
        from data_fetcher import DataFetcher
        data_fetcher = DataFetcher()
        
        test_data = data_fetcher.get_real_time_data("AAPL")
        if test_data:
            print("✅ Data fetching works")
        else:
            print("⚠️  Data fetching returned no data (might be market hours)")
        
        # Test strategies
        from trading_strategies import StrategyManager
        strategy_manager = StrategyManager()
        print("✅ Trading strategies loaded")
        
        # Test backtesting
        from backtesting_engine import BacktestingEngine
        backtesting_engine = BacktestingEngine()
        print("✅ Backtesting engine initialized")
        
        # Test SMS (configuration only)
        from sms_notifier import SMSNotifier
        sms_notifier = SMSNotifier()
        if sms_notifier.is_configured():
            print("✅ SMS is configured and ready")
        else:
            print("⚠️  SMS is not configured (optional)")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("   Try installing dependencies again")
        return False
    except Exception as e:
        print(f"❌ Error testing functionality: {e}")
        return False

def run_demo():
    """Ask user if they want to run the demo"""
    user_input = input("\nWould you like to run the demonstration? (y/N): ").strip().lower()
    
    if user_input == 'y':
        print("🎬 Starting demonstration...")
        try:
            subprocess.run([sys.executable, "demo.py"])
        except KeyboardInterrupt:
            print("\n⏹️  Demo interrupted")
        except Exception as e:
            print(f"❌ Error running demo: {e}")
    else:
        print("⏭️  Skipping demonstration")

def show_next_steps():
    """Show next steps to the user"""
    print_header("NEXT STEPS")
    
    print("🎯 Your finance bot is ready! Here's what you can do next:")
    print()
    print("1. 📝 Configure your settings:")
    print("   - Edit .env file with your Twilio credentials")
    print("   - Add your phone number to SMS_RECIPIENTS")
    print("   - Optionally add Alpha Vantage API key")
    print()
    print("2. 🧪 Test the bot:")
    print("   python demo.py")
    print()
    print("3. 🚀 Start the full bot:")
    print("   python finance_bot.py")
    print()
    print("4. 📚 Read the documentation:")
    print("   - Check README.md for detailed instructions")
    print("   - Review trading strategies and configuration options")
    print()
    print("5. 🛠️  Customize:")
    print("   - Modify WATCHLIST in .env")
    print("   - Adjust UPDATE_INTERVAL_MINUTES")
    print("   - Add custom trading strategies")
    print()
    print("💡 Pro Tips:")
    print("   - Start with paper trading (default configuration)")
    print("   - Monitor the bot during market hours for best results")
    print("   - Check logs for any issues or errors")

def main():
    """Main quick start function"""
    print_header("FINANCE BOT QUICK START")
    print("🎯 This script will help you set up and test your finance bot")
    print("📋 Follow the steps below to get started")
    
    # Step 1: Check Python version
    print_step(1, "Checking Python Version")
    if not check_python_version():
        print("\n❌ Setup failed: Python version incompatible")
        return
    
    # Step 2: Install dependencies
    print_step(2, "Installing Dependencies")
    if not install_dependencies():
        print("\n❌ Setup failed: Could not install dependencies")
        return
    
    # Step 3: Set up environment
    print_step(3, "Setting Up Environment")
    if not setup_environment():
        print("\n❌ Setup failed: Could not set up environment")
        return
    
    # Step 4: Test functionality
    print_step(4, "Testing Basic Functionality")
    if not test_basic_functionality():
        print("\n⚠️  Some tests failed, but you can continue")
        print("   Check the error messages above")
    
    # Step 5: Optional demo
    print_step(5, "Optional Demonstration")
    run_demo()
    
    # Show next steps
    show_next_steps()
    
    print_header("SETUP COMPLETE")
    print("🎉 Your finance bot is ready to use!")
    print("🚀 Run 'python finance_bot.py' to start trading!")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⏹️  Setup interrupted by user")
    except Exception as e:
        print(f"\n❌ Unexpected error during setup: {e}")
        print("🔧 Please check the error message and try again")