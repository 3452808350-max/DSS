#!/usr/bin/env python3
"""
Test Alpha Vantage API with your key
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import requests
import time
from config.settings import API_CONFIG

def test_alpha_vantage():
    """Test Alpha Vantage API"""
    print("🔑 Testing Alpha Vantage API...")
    print(f"API Key: {API_CONFIG.ALPHA_VANTAGE_API_KEY[:8]}...")
    print()
    
    # Test symbols
    test_symbols = [
        ("Apple", "AAPL", "US"),
        ("Microsoft", "MSFT", "US"),
        ("Tencent", "0700.HK", "HK"),
        ("Alibaba", "BABA", "US"),  # US-listed
    ]
    
    results = []
    
    for name, symbol, market in test_symbols:
        print(f"Fetching {name} ({symbol})...")
        
        url = "https://www.alphavantage.co/query"
        params = {
            'function': 'GLOBAL_QUOTE',
            'symbol': symbol,
            'apikey': API_CONFIG.ALPHA_VANTAGE_API_KEY
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            
            if 'Global Quote' in data:
                quote = data['Global Quote']
                price = quote.get('05. price', 'N/A')
                change = quote.get('10. change percent', 'N/A')
                volume = quote.get('06. volume', 'N/A')
                
                results.append({
                    'name': name,
                    'symbol': symbol,
                    'market': market,
                    'price': price,
                    'change': change,
                    'volume': volume,
                    'status': 'SUCCESS'
                })
                
                print(f"  ✅ Price: ${price}, Change: {change}")
                
            elif 'Note' in data:
                note = data['Note'][:80] + "..." if len(data['Note']) > 80 else data['Note']
                print(f"  ⚠️  Note: {note}")
                results.append({
                    'name': name,
                    'symbol': symbol,
                    'market': market,
                    'status': 'RATE_LIMIT',
                    'note': note
                })
                
            elif 'Error Message' in data:
                print(f"  ❌ Error: {data['Error Message']}")
                results.append({
                    'name': name,
                    'symbol': symbol,
                    'market': market,
                    'status': 'ERROR',
                    'error': data['Error Message']
                })
            else:
                print(f"  ❓ Unexpected response")
                results.append({
                    'name': name,
                    'symbol': symbol,
                    'market': market,
                    'status': 'UNKNOWN',
                    'data': data
                })
                
        except Exception as e:
            print(f"  ❌ Exception: {e}")
            results.append({
                'name': name,
                'symbol': symbol,
                'market': market,
                'status': 'EXCEPTION',
                'error': str(e)
            })
        
        # Respect rate limits (5 calls per minute = 12 seconds between calls)
        if symbol != test_symbols[-1][1]:  # Don't wait after last call
            print("  Waiting 12 seconds for rate limit...")
            time.sleep(12)
    
    return results

def analyze_results(results):
    """Analyze API test results"""
    print("\n" + "="*60)
    print("API TEST RESULTS")
    print("="*60)
    
    success_count = sum(1 for r in results if r['status'] == 'SUCCESS')
    total_count = len(results)
    
    print(f"\n📊 Summary: {success_count}/{total_count} successful")
    
    if success_count > 0:
        print("\n✅ SUCCESSFUL FETCHES:")
        print("-"*40)
        for r in results:
            if r['status'] == 'SUCCESS':
                print(f"{r['name']:15} ({r['symbol']:10}) ${r['price']:>10} {r['change']:>10}")
    
    # Check for issues
    issues = [r for r in results if r['status'] != 'SUCCESS']
    if issues:
        print("\n⚠️  ISSUES FOUND:")
        print("-"*40)
        for r in issues:
            print(f"{r['name']} ({r['symbol']}): {r['status']}")
            if 'note' in r:
                print(f"  Note: {r['note']}")
            if 'error' in r:
                print(f"  Error: {r['error'][:100]}...")
    
    return success_count, total_count

def recommendations(success_count, total_count):
    """Provide recommendations based on test results"""
    print("\n" + "="*60)
    print("RECOMMENDATIONS")
    print("="*60)
    
    if success_count == total_count:
        print("🎉 Excellent! All API calls successful.")
        print("\nNext steps:")
        print("1. Expand stock list in config/settings.py")
        print("2. Implement batch data collection with rate limiting")
        print("3. Add data validation and error handling")
        
    elif success_count > 0:
        print("⚠️  Partial success. Some API calls worked.")
        print("\nPossible issues:")
        print("1. Rate limiting (free tier: 5 calls/minute)")
        print("2. Invalid symbols for certain markets")
        print("3. Network issues")
        
        print("\nSolutions:")
        print("1. Add delays between API calls (already implemented)")
        print("2. Cache frequently accessed data")
        print("3. Implement retry logic for failed calls")
        print("4. Use multiple data sources as fallback")
        
    else:
        print("❌ No API calls succeeded.")
        print("\nTroubleshooting:")
        print("1. Check API key validity")
        print("2. Check internet connection")
        print("3. Verify symbol formats")
        print("4. Check Alpha Vantage service status")
    
    print("\n🔧 Technical notes:")
    print(f"- API Key: {API_CONFIG.ALPHA_VANTAGE_API_KEY[:8]}...")
    print("- Rate limit: 5 calls per minute (free tier)")
    print("- Best for: US stocks, some international")
    print("- Limitations: Limited A-share data")

def main():
    """Main function"""
    print("analyse - API Test")
    print("="*60)
    
    try:
        # Test API
        results = test_alpha_vantage()
        
        # Analyze results
        success_count, total_count = analyze_results(results)
        
        # Provide recommendations
        recommendations(success_count, total_count)
        
        print("\n" + "="*60)
        print("TEST COMPLETE")
        print("="*60)
        
        if success_count > 0:
            print("✅ API is working! You can proceed with development.")
        else:
            print("❌ API test failed. Please fix issues before proceeding.")
            
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Error during API test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()