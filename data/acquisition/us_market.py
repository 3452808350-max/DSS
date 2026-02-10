"""
US Market Data Acquisition Module
"""

import requests
import time
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

from config.settings import API_CONFIG, MARKET_CONFIG

# Set up logging
logger = logging.getLogger(__name__)

class USMarketDataFetcher:
    """Fetches US market data from Alpha Vantage API"""
    
    def __init__(self):
        self.api_key = API_CONFIG.ALPHA_VANTAGE_API_KEY
        self.base_url = "https://www.alphavantage.co/query"
        self.rate_limit_delay = 12  # seconds (5 calls/minute = 12 seconds between calls)
        
    def get_stock_quote(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get real-time quote for a US stock
        
        Args:
            symbol: Stock symbol (e.g., 'AAPL')
            
        Returns:
            Dictionary with quote data or None if failed
        """
        params = {
            'function': 'GLOBAL_QUOTE',
            'symbol': symbol,
            'apikey': self.api_key
        }
        
        try:
            logger.info(f"Fetching quote for {symbol}")
            response = requests.get(self.base_url, params=params, timeout=10)
            data = response.json()
            
            if 'Global Quote' in data:
                quote = data['Global Quote']
                return self._parse_quote(quote, symbol)
            elif 'Note' in data:
                logger.warning(f"Rate limit note for {symbol}: {data['Note'][:50]}...")
                return None
            elif 'Error Message' in data:
                logger.error(f"API error for {symbol}: {data['Error Message']}")
                return None
            else:
                logger.warning(f"Unexpected response for {symbol}: {data}")
                return None
                
        except requests.exceptions.Timeout:
            logger.error(f"Timeout fetching {symbol}")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error for {symbol}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error for {symbol}: {e}")
            return None
    
    def _parse_quote(self, quote: Dict[str, str], symbol: str) -> Dict[str, Any]:
        """Parse Alpha Vantage quote response"""
        try:
            return {
                'symbol': symbol,
                'timestamp': datetime.now().isoformat(),
                'price': float(quote.get('05. price', 0)),
                'change': float(quote.get('09. change', 0)),
                'change_percent': float(quote.get('10. change percent', '0%').replace('%', '')),
                'volume': int(quote.get('06. volume', 0)),
                'previous_close': float(quote.get('08. previous close', 0)),
                'open': float(quote.get('02. open', 0)),
                'high': float(quote.get('03. high', 0)),
                'low': float(quote.get('04. low', 0)),
                'latest_trading_day': quote.get('07. latest trading day', ''),
                'data_source': 'alpha_vantage',
            }
        except (ValueError, TypeError) as e:
            logger.error(f"Error parsing quote for {symbol}: {e}")
            return {}
    
    def get_batch_quotes(self, symbols: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        Get quotes for multiple stocks with rate limiting
        
        Args:
            symbols: List of stock symbols
            
        Returns:
            Dictionary mapping symbols to quote data
        """
        results = {}
        
        for i, symbol in enumerate(symbols):
            quote = self.get_stock_quote(symbol)
            if quote:
                results[symbol] = quote
            
            # Respect rate limits (skip delay for last symbol)
            if i < len(symbols) - 1:
                logger.debug(f"Waiting {self.rate_limit_delay}s for rate limit...")
                time.sleep(self.rate_limit_delay)
        
        logger.info(f"Fetched {len(results)}/{len(symbols)} quotes successfully")
        return results
    
    def get_intraday_data(self, symbol: str, interval: str = '5min') -> Optional[Dict[str, Any]]:
        """
        Get intraday data for a stock
        
        Args:
            symbol: Stock symbol
            interval: Time interval (1min, 5min, 15min, 30min, 60min)
            
        Returns:
            Dictionary with intraday data or None if failed
        """
        params = {
            'function': 'TIME_SERIES_INTRADAY',
            'symbol': symbol,
            'interval': interval,
            'apikey': self.api_key,
            'outputsize': 'compact'  # Last 100 data points
        }
        
        try:
            logger.info(f"Fetching intraday data for {symbol} ({interval})")
            response = requests.get(self.base_url, params=params, timeout=10)
            data = response.json()
            
            if f'Time Series ({interval})' in data:
                time_series = data[f'Time Series ({interval})']
                return self._parse_intraday_data(time_series, symbol, interval)
            elif 'Note' in data:
                logger.warning(f"Rate limit note for intraday {symbol}: {data['Note'][:50]}...")
                return None
            else:
                logger.warning(f"Unexpected intraday response for {symbol}: {data}")
                return None
                
        except Exception as e:
            logger.error(f"Error fetching intraday data for {symbol}: {e}")
            return None
    
    def _parse_intraday_data(self, time_series: Dict[str, Dict[str, str]], 
                            symbol: str, interval: str) -> Dict[str, Any]:
        """Parse intraday time series data"""
        parsed_data = []
        
        for timestamp, values in time_series.items():
            try:
                parsed_data.append({
                    'timestamp': timestamp,
                    'open': float(values['1. open']),
                    'high': float(values['2. high']),
                    'low': float(values['3. low']),
                    'close': float(values['4. close']),
                    'volume': int(values['5. volume']),
                })
            except (ValueError, KeyError) as e:
                logger.warning(f"Error parsing intraday point for {symbol}: {e}")
                continue
        
        # Sort by timestamp (newest first)
        parsed_data.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return {
            'symbol': symbol,
            'interval': interval,
            'data_points': parsed_data,
            'count': len(parsed_data),
            'latest_timestamp': parsed_data[0]['timestamp'] if parsed_data else None,
            'data_source': 'alpha_vantage',
        }
    
    def get_default_watchlist_quotes(self) -> Dict[str, Dict[str, Any]]:
        """
        Get quotes for default US watchlist
        
        Returns:
            Dictionary mapping symbols to quote data
        """
        default_symbols = MARKET_CONFIG.DEFAULT_WATCHLIST['US']
        return self.get_batch_quotes(default_symbols)

# Convenience function
def fetch_us_market_data(symbols: Optional[List[str]] = None) -> Dict[str, Dict[str, Any]]:
    """
    Convenience function to fetch US market data
    
    Args:
        symbols: List of symbols to fetch (uses default watchlist if None)
        
    Returns:
        Dictionary mapping symbols to quote data
    """
    fetcher = USMarketDataFetcher()
    
    if symbols is None:
        symbols = MARKET_CONFIG.DEFAULT_WATCHLIST['US']
    
    return fetcher.get_batch_quotes(symbols)

# Example usage
if __name__ == "__main__":
    # Set up basic logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("Testing US Market Data Fetcher")
    print("="*60)
    
    fetcher = USMarketDataFetcher()
    
    # Test single quote
    print("\n1. Testing single stock quote (AAPL):")
    aapl_quote = fetcher.get_stock_quote("AAPL")
    if aapl_quote:
        print(f"   ✅ AAPL: ${aapl_quote['price']:.2f} ({aapl_quote['change_percent']:.2f}%)")
    else:
        print("   ❌ Failed to fetch AAPL")
    
    # Test batch quotes (small batch to respect rate limits)
    print("\n2. Testing batch quotes (2 stocks):")
    test_symbols = ["MSFT", "GOOGL"]
    batch_quotes = fetcher.get_batch_quotes(test_symbols)
    
    for symbol, quote in batch_quotes.items():
        print(f"   ✅ {symbol}: ${quote['price']:.2f} ({quote['change_percent']:.2f}%)")
    
    print(f"\n📊 Fetched {len(batch_quotes)}/{len(test_symbols)} quotes successfully")
    
    # Test default watchlist (commented out to avoid rate limits)
    # print("\n3. Testing default watchlist:")
    # watchlist_quotes = fetcher.get_default_watchlist_quotes()
    # print(f"   Fetched {len(watchlist_quotes)} stocks from default watchlist")