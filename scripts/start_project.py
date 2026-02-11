#!/usr/bin/env python3
"""
analyse - Project Starter Script
Initializes the project and tests basic functionality
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.settings import get_all_configs

def print_banner():
    """Print project banner"""
    banner = """
    ╔══════════════════════════════════════════════════════════╗
    ║      Stock Analysis Decision Support System (DSS)        ║
    ║                    Project Initialization                ║
    ╚══════════════════════════════════════════════════════════╝
    """
    print(banner)

def check_directories():
    """Check if project directories exist"""
    print("📁 Checking project structure...")
    
    directories = [
        project_root / "data",
        project_root / "analysis",
        project_root / "decision", 
        project_root / "integration",
        project_root / "config",
        project_root / "tests",
        project_root / "docs",
        project_root / "scripts",
        project_root / "logs",
        project_root / "reports",
    ]
    
    all_exist = True
    for directory in directories:
        if directory.exists():
            print(f"   ✅ {directory.name}/")
        else:
            print(f"   ❌ {directory.name}/ (missing)")
            all_exist = False
    
    return all_exist

def check_configuration():
    """Check configuration settings"""
    print("\n⚙️  Checking configuration...")
    
    try:
        configs = get_all_configs()
        
        # Check API key
        api_key = configs["api"].ALPHA_VANTAGE_API_KEY
        if api_key and api_key != "MXAYBEBGFHR6PHYW":
            print(f"   ✅ Alpha Vantage API key: {api_key[:8]}...")
        else:
            print(f"   ⚠️  Alpha Vantage API key: Using default/test key")
        
        # Check database
        db_config = configs["database"]
        print(f"   ✅ Database: {db_config.ACTIVE_DB.upper()}")
        
        # Check market config
        market_config = configs["market"]
        print(f"   ✅ Markets configured: {', '.join(market_config.TRADING_HOURS.keys())}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Configuration error: {e}")
        return False

def check_dependencies():
    """Check if required packages are installed"""
    print("\n📦 Checking dependencies...")
    
    required_packages = [
        "pandas",
        "numpy", 
        "requests",
        "yfinance",
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package)
            print(f"   ✅ {package}")
        except ImportError:
            print(f"   ❌ {package} (missing)")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n⚠️  Missing packages: {', '.join(missing_packages)}")
        print("   Install with: pip install " + " ".join(missing_packages))
        return False
    
    return True

def create_sample_files():
    """Create sample files for testing"""
    print("\n📝 Creating sample files...")
    
    # Create a sample data file
    sample_data = project_root / "data" / "sample_stocks.csv"
    sample_content = """symbol,name,market,currency
AAPL,Apple Inc.,US,USD
MSFT,Microsoft Corporation,US,USD
0700.HK,Tencent Holdings Ltd.,HK,HKD
600519.SS,Kweichow Moutai Co.,CN,CNY
"""
    
    try:
        with open(sample_data, "w") as f:
            f.write(sample_content)
        print(f"   ✅ Created {sample_data.name}")
    except Exception as e:
        print(f"   ❌ Failed to create sample file: {e}")
        return False
    
    return True

def next_steps():
    """Display next steps"""
    print("\n" + "="*60)
    print("NEXT STEPS")
    print("="*60)
    
    steps = [
        "1. Review project structure in /home/kyj/文档/code/",
        "2. Read README.md for project overview",
        "3. Review TASKS.md for implementation plan", 
        "4. Set up virtual environment: python -m venv venv",
        "5. Install dependencies: pip install -r requirements.txt",
        "6. Test Alpha Vantage API with your key",
        "7. Start with Week 1 tasks in TASKS.md",
    ]
    
    for step in steps:
        print(f"   {step}")
    
    print("\n🎯 Immediate action: Test API key with quick_stock_check.py")

def main():
    """Main function"""
    print_banner()
    
    print(f"Project root: {project_root}")
    print(f"Python: {sys.version}\n")
    
    # Run checks
    dirs_ok = check_directories()
    config_ok = check_configuration()
    deps_ok = check_dependencies()
    samples_ok = create_sample_files()
    
    # Summary
    print("\n" + "="*60)
    print("SETUP SUMMARY")
    print("="*60)
    
    checks = [
        ("Project structure", dirs_ok),
        ("Configuration", config_ok),
        ("Dependencies", deps_ok),
        ("Sample files", samples_ok),
    ]
    
    all_passed = True
    for check_name, passed in checks:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} {check_name}")
        if not passed:
            all_passed = False
    
    if all_passed:
        print("\n🎉 Project setup completed successfully!")
    else:
        print("\n⚠️  Some checks failed. Please fix issues before proceeding.")
    
    # Show next steps
    next_steps()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Setup interrupted by user")
    except Exception as e:
        print(f"\n❌ Error during setup: {e}")
        import traceback
        traceback.print_exc()