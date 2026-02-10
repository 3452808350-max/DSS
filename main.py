#!/usr/bin/env python3
"""
Stock Analysis DSS - Main Entry Point
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

import argparse
import logging
from datetime import datetime

from config.settings import get_all_configs
from data.acquisition.us_market import fetch_us_market_data

def setup_logging():
    """Set up logging configuration"""
    from config.settings import LOGGING_CONFIG
    
    logging.basicConfig(
        level=getattr(logging, LOGGING_CONFIG.LOG_LEVEL),
        format=LOGGING_CONFIG.LOG_FORMAT,
        handlers=[
            logging.FileHandler(LOGGING_CONFIG.LOG_FILE),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    return logging.getLogger(__name__)

def print_banner():
    """Print application banner"""
    banner = """
    ╔══════════════════════════════════════════════════════════╗
    ║      Stock Analysis Decision Support System (DSS)        ║
    ║                    Version 0.1.0                         ║
    ╚══════════════════════════════════════════════════════════╝
    """
    print(banner)

def fetch_data_command(args):
    """Fetch market data command"""
    logger = logging.getLogger(__name__)
    logger.info("Starting data fetch command")
    
    print("\n📊 FETCHING MARKET DATA")
    print("="*60)
    
    # Fetch US market data
    print("\n🇺🇸 US Market Data:")
    print("-"*40)
    
    try:
        us_data = fetch_us_market_data()
        
        if us_data:
            print(f"✅ Successfully fetched {len(us_data)} stocks")
            
            # Display summary
            gainers = sum(1 for d in us_data.values() if d['change_percent'] > 0)
            losers = sum(1 for d in us_data.values() if d['change_percent'] < 0)
            
            print(f"\n📈 Gainers: {gainers}, 📉 Losers: {losers}")
            
            # Show top movers
            sorted_stocks = sorted(us_data.items(), 
                                 key=lambda x: x[1]['change_percent'], 
                                 reverse=True)
            
            print("\n🏆 Top Performers:")
            for symbol, data in sorted_stocks[:3]:
                change = data['change_percent']
                icon = "🟢" if change > 0 else "🔴" if change < 0 else "🟡"
                print(f"{icon} {symbol}: ${data['price']:.2f} ({change:+.2f}%)")
            
            print("\n📦 Bottom Performers:")
            for symbol, data in sorted_stocks[-3:]:
                change = data['change_percent']
                icon = "🟢" if change > 0 else "🔴" if change < 0 else "🟡"
                print(f"{icon} {symbol}: ${data['price']:.2f} ({change:+.2f}%)")
            
            # Save data if requested
            if args.save:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = project_root / "data" / f"us_market_{timestamp}.json"
                
                import json
                with open(filename, 'w') as f:
                    json.dump(us_data, f, indent=2, default=str)
                
                print(f"\n💾 Data saved to: {filename}")
                
        else:
            print("❌ Failed to fetch US market data")
            
    except Exception as e:
        logger.error(f"Error fetching data: {e}")
        print(f"❌ Error: {e}")

def test_command(args):
    """Test system components command"""
    logger = logging.getLogger(__name__)
    logger.info("Starting test command")
    
    print("\n🧪 SYSTEM TESTS")
    print("="*60)
    
    # Test configuration
    print("\n1. Testing configuration...")
    try:
        configs = get_all_configs()
        print("   ✅ Configuration loaded successfully")
        print(f"   📁 Project root: {project_root}")
        print(f"   🔑 API Key: {configs['api'].ALPHA_VANTAGE_API_KEY[:8]}...")
    except Exception as e:
        print(f"   ❌ Configuration error: {e}")
    
    # Test data acquisition
    print("\n2. Testing data acquisition...")
    try:
        from data.acquisition.us_market import USMarketDataFetcher
        fetcher = USMarketDataFetcher()
        print("   ✅ US Market Data Fetcher initialized")
        
        # Test single quote (with error handling)
        test_symbol = "AAPL"
        quote = fetcher.get_stock_quote(test_symbol)
        if quote:
            print(f"   ✅ {test_symbol} quote: ${quote['price']:.2f}")
        else:
            print(f"   ⚠️  Could not fetch {test_symbol} (may be rate limited)")
            
    except Exception as e:
        print(f"   ❌ Data acquisition error: {e}")
    
    # Test directories
    print("\n3. Testing project structure...")
    required_dirs = [
        project_root / "data",
        project_root / "analysis",
        project_root / "decision",
        project_root / "config",
        project_root / "logs",
    ]
    
    all_exist = True
    for directory in required_dirs:
        if directory.exists():
            print(f"   ✅ {directory.name}/")
        else:
            print(f"   ❌ {directory.name}/ (missing)")
            all_exist = False
    
    if all_exist:
        print("\n🎉 All tests passed!")
    else:
        print("\n⚠️  Some tests failed. Please check project structure.")

def info_command(args):
    """Display system information command"""
    print("\n📋 SYSTEM INFORMATION")
    print("="*60)
    
    # Project info
    print(f"\n🏠 Project: Stock Analysis DSS")
    print(f"   Version: 0.1.0")
    print(f"   Path: {project_root}")
    
    # Configuration info
    configs = get_all_configs()
    
    print(f"\n⚙️  Configuration:")
    print(f"   API Key: {configs['api'].ALPHA_VANTAGE_API_KEY[:8]}...")
    print(f"   Database: {configs['database'].ACTIVE_DB.upper()}")
    
    # Market info
    print(f"\n🌎 Markets:")
    for market, hours in configs['market'].TRADING_HOURS.items():
        print(f"   {market}: {hours['open']} - {hours['close']} (Beijing time)")
    
    # Default watchlist
    print(f"\n📈 Default Watchlist:")
    for market, symbols in configs['market'].DEFAULT_WATCHLIST.items():
        print(f"   {market}: {len(symbols)} symbols")
    
    # System status
    print(f"\n📊 System Status:")
    print(f"   Python: {sys.version.split()[0]}")
    print(f"   Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Check market hours
    now = datetime.now()
    hour = now.hour
    print(f"\n🕒 Current Market Status (Beijing Time):")
    print(f"   Current: {hour:02d}:{now.minute:02d}")
    
    us_open = (hour == 22 and now.minute >= 30) or (hour > 22) or (hour < 5)
    hk_open = 9 <= hour < 16
    cn_open = 9 <= hour < 15
    
    print(f"   US Market: {'🟢 OPEN' if us_open else '🔴 CLOSED'}")
    print(f"   HK Market: {'🟢 OPEN' if hk_open else '🔴 CLOSED'}")
    print(f"   A-Shares:  {'🟢 OPEN' if cn_open else '🔴 CLOSED'}")

def main():
    """Main entry point"""
    # Set up argument parser
    parser = argparse.ArgumentParser(
        description="Stock Analysis Decision Support System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s fetch           # Fetch market data
  %(prog)s fetch --save    # Fetch and save data
  %(prog)s test            # Run system tests
  %(prog)s info            # Show system information
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Fetch command
    fetch_parser = subparsers.add_parser('fetch', help='Fetch market data')
    fetch_parser.add_argument('--save', action='store_true', help='Save fetched data to file')
    
    # Test command
    test_parser = subparsers.add_parser('test', help='Test system components')
    
    # Info command
    info_parser = subparsers.add_parser('info', help='Show system information')
    
    # Parse arguments
    args = parser.parse_args()
    
    # Set up logging
    logger = setup_logging()
    
    # Print banner
    print_banner()
    
    # Execute command
    if args.command == 'fetch':
        fetch_data_command(args)
    elif args.command == 'test':
        test_command(args)
    elif args.command == 'info':
        info_command(args)
    else:
        # No command specified, show help
        parser.print_help()
        
        # Show quick start
        print("\n" + "="*60)
        print("QUICK START")
        print("="*60)
        print("\nTo get started:")
        print("1. Run tests: python main.py test")
        print("2. Fetch data: python main.py fetch")
        print("3. Check info: python main.py info")
        print("\nFor more details, see README.md and TASKS.md")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Operation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)