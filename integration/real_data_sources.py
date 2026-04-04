"""
真实数据源集成模块
直接使用提供的API密钥获取真实市场数据
"""

import sys
import asyncio
import aiohttp
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import logging
import json
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from collections import OrderedDict
import time
import requests

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

logger = logging.getLogger(__name__)


@dataclass
class SentimentCache:
    """
    情绪数据缓存项
    """
    data: Dict[str, Any]
    timestamp: float
    ttl: int = 300  # 默认5分钟 TTL

    def is_expired(self) -> bool:
        """检查缓存是否过期"""
        return time.time() - self.timestamp > self.ttl


class AsyncSentimentAnalyzer:
    """
    异步情绪分析器
    使用 asyncio 和 aiohttp 并发获取多个数据源的情绪数据
    """

    # 缓存 TTL (秒)
    DEFAULT_CACHE_TTL = 300  # 5分钟

    def __init__(
        self,
        news_api_key: Optional[str] = None,
        twitter_bearer_token: Optional[str] = None,
        cache_ttl: int = DEFAULT_CACHE_TTL
    ):
        """
        初始化异步情绪分析器

        Args:
            news_api_key: NewsAPI 密钥（可选）
            twitter_bearer_token: Twitter/X Bearer Token（可选）
            cache_ttl: 缓存 TTL（秒），默认 5 分钟
        """
        self.news_api_key = news_api_key
        self.twitter_bearer_token = twitter_bearer_token

        # API 端点
        self.endpoints = {
            'reddit': 'https://api.tradestie.com/v1/apps/reddit',
            'news': 'https://newsapi.org/v2/everything',
            'twitter': 'https://api.twitter.com/2/tweets/search/recent'
        }

        # 缓存：使用 OrderedDict 实现 LRU
        self._cache: OrderedDict[str, SentimentCache] = OrderedDict()
        self._cache_ttl = cache_ttl
        self._cache_max_size = 100  # 最大缓存条目数

        # aiohttp session (延迟初始化)
        self._session: Optional[aiohttp.ClientSession] = None

        logger.info("异步情绪分析器初始化完成")

    async def _get_session(self) -> aiohttp.ClientSession:
        """获取或创建 aiohttp session"""
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=30)
            self._session = aiohttp.ClientSession(timeout=timeout)
        return self._session

    async def close(self):
        """关闭 aiohttp session"""
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None

    def _get_cache_key(self, source: str, ticker: str) -> str:
        """生成缓存键"""
        return f"{source}:{ticker}"

    def _get_from_cache(self, source: str, ticker: str) -> Optional[Dict[str, Any]]:
        """从缓存获取数据"""
        key = self._get_cache_key(source, ticker)

        if key in self._cache:
            cache_item = self._cache[key]
            if not cache_item.is_expired():
                # 移动到末尾（LRU）
                self._cache.move_to_end(key)
                logger.debug(f"缓存命中: {key}")
                return cache_item.data
            else:
                # 缓存过期，删除
                del self._cache[key]
                logger.debug(f"缓存过期: {key}")

        return None

    def _set_cache(self, source: str, ticker: str, data: Dict[str, Any]):
        """设置缓存"""
        key = self._get_cache_key(source, ticker)

        # 如果缓存已满，删除最旧的条目
        if len(self._cache) >= self._cache_max_size:
            oldest_key = next(iter(self._cache))
            del self._cache[oldest_key]
            logger.debug(f"缓存已满，删除: {oldest_key}")

        self._cache[key] = SentimentCache(
            data=data,
            timestamp=time.time(),
            ttl=self._cache_ttl
        )
        logger.debug(f"缓存设置: {key}")

    async def fetch_reddit_sentiment(self, ticker: str) -> Dict[str, Any]:
        """
        异步获取 Reddit 情绪数据（通过 Tradestie API）

        Args:
            ticker: 股票代码

        Returns:
            Reddit 情绪数据
        """
        # 检查缓存
        cached = self._get_from_cache('reddit', ticker)
        if cached is not None:
            return cached

        try:
            session = await self._get_session()
            url = self.endpoints['reddit']
            params = {'ticker': ticker}

            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()

                    # 计算情绪分数
                    sentiment_score = self._calculate_reddit_sentiment(data)

                    result = {
                        'source': 'reddit',
                        'ticker': ticker,
                        'data': data,
                        'sentiment_score': sentiment_score,
                        'timestamp': datetime.now().isoformat()
                    }

                    # 缓存结果
                    self._set_cache('reddit', ticker, result)
                    logger.info(f"成功获取 Reddit 情绪数据: {ticker}")
                    return result
                else:
                    logger.error(f"Reddit API 错误: {response.status}")
                    return {
                        'source': 'reddit',
                        'ticker': ticker,
                        'error': f"API错误: {response.status}",
                        'timestamp': datetime.now().isoformat()
                    }

        except asyncio.TimeoutError:
            logger.error(f"Reddit API 超时: {ticker}")
            return {
                'source': 'reddit',
                'ticker': ticker,
                'error': '请求超时',
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"获取 Reddit 情绪数据时出错: {e}")
            return {
                'source': 'reddit',
                'ticker': ticker,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

    async def fetch_news_sentiment(self, ticker: str, days: int = 7) -> Dict[str, Any]:
        """
        异步获取新闻情绪数据（通过 NewsAPI）

        Args:
            ticker: 股票代码
            days: 查询最近几天的新闻，默认 7 天

        Returns:
            新闻情绪数据
        """
        # 如果没有配置 NewsAPI 密钥，返回占位符
        if not self.news_api_key:
            return {
                'source': 'news',
                'ticker': ticker,
                'error': 'NewsAPI 密钥未配置',
                'timestamp': datetime.now().isoformat()
            }

        # 检查缓存
        cached = self._get_from_cache('news', ticker)
        if cached is not None:
            return cached

        try:
            session = await self._get_session()
            url = self.endpoints['news']

            # 计算日期范围
            to_date = datetime.now()
            from_date = to_date - timedelta(days=days)

            params = {
                'q': ticker,
                'from': from_date.strftime('%Y-%m-%d'),
                'to': to_date.strftime('%Y-%m-%d'),
                'sortBy': 'publishedAt',
                'apiKey': self.news_api_key,
                'language': 'en',
                'pageSize': 50
            }

            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()

                    # 计算新闻情绪
                    sentiment_score = self._calculate_news_sentiment(data)

                    result = {
                        'source': 'news',
                        'ticker': ticker,
                        'total_articles': data.get('totalResults', 0),
                        'articles': data.get('articles', [])[:10],  # 只保留前10篇
                        'sentiment_score': sentiment_score,
                        'timestamp': datetime.now().isoformat()
                    }

                    # 缓存结果
                    self._set_cache('news', ticker, result)
                    logger.info(f"成功获取新闻情绪数据: {ticker}")
                    return result
                else:
                    logger.error(f"NewsAPI 错误: {response.status}")
                    return {
                        'source': 'news',
                        'ticker': ticker,
                        'error': f"API错误: {response.status}",
                        'timestamp': datetime.now().isoformat()
                    }

        except asyncio.TimeoutError:
            logger.error(f"NewsAPI 超时: {ticker}")
            return {
                'source': 'news',
                'ticker': ticker,
                'error': '请求超时',
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"获取新闻情绪数据时出错: {e}")
            return {
                'source': 'news',
                'ticker': ticker,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

    async def fetch_twitter_sentiment(self, ticker: str) -> Dict[str, Any]:
        """
        异步获取 Twitter/X 情绪数据

        注意：Twitter API v2 需要 Academic Research 或 Basic Pro 访问权限

        Args:
            ticker: 股票代码

        Returns:
            Twitter 情绪数据
        """
        # 如果没有配置 Twitter Token，返回占位符
        if not self.twitter_bearer_token:
            return {
                'source': 'twitter',
                'ticker': ticker,
                'error': 'Twitter/X API 未配置（需要 Academic Research 或 Pro 权限）',
                'timestamp': datetime.now().isoformat()
            }

        # 检查缓存
        cached = self._get_from_cache('twitter', ticker)
        if cached is not None:
            return cached

        try:
            session = await self._get_session()
            url = self.endpoints['twitter']

            headers = {
                'Authorization': f'Bearer {self.twitter_bearer_token}'
            }

            params = {
                'query': f'${ticker} -is:retweet lang:en',
                'max_results': 100,
                'tweet.fields': 'created_at,public_metrics'
            }

            async with session.get(url, headers=headers, params=params) as response:
                if response.status == 200:
                    data = await response.json()

                    # 计算情绪分数
                    sentiment_score = self._calculate_twitter_sentiment(data)

                    result = {
                        'source': 'twitter',
                        'ticker': ticker,
                        'tweet_count': len(data.get('data', [])),
                        'tweets': data.get('data', [])[:20],  # 保留前20条
                        'sentiment_score': sentiment_score,
                        'timestamp': datetime.now().isoformat()
                    }

                    # 缓存结果
                    self._set_cache('twitter', ticker, result)
                    logger.info(f"成功获取 Twitter 情绪数据: {ticker}")
                    return result
                else:
                    logger.error(f"Twitter API 错误: {response.status}")
                    return {
                        'source': 'twitter',
                        'ticker': ticker,
                        'error': f"API错误: {response.status}",
                        'timestamp': datetime.now().isoformat()
                    }

        except asyncio.TimeoutError:
            logger.error(f"Twitter API 超时: {ticker}")
            return {
                'source': 'twitter',
                'ticker': ticker,
                'error': '请求超时',
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"获取 Twitter 情绪数据时出错: {e}")
            return {
                'source': 'twitter',
                'ticker': ticker,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

    async def async_fetch_sentiment(
        self,
        tickers: List[str],
        sources: Optional[List[str]] = None
    ) -> Dict[str, Dict[str, Any]]:
        """
        异步并发获取多个股票的情绪数据

        Args:
            tickers: 股票代码列表
            sources: 数据源列表，可选 ['reddit', 'news', 'twitter']
                    如果为 None，则获取所有可用来源

        Returns:
            按股票代码分组的情绪数据
        """
        if sources is None:
            sources = ['reddit', 'news', 'twitter']

        logger.info(f"开始异步获取 {len(tickers)} 只股票的情绪数据，数据源: {sources}")

        results: Dict[str, Dict[str, Any]] = {}

        # 为每个股票创建所有数据源的并发任务
        tasks = []
        ticker_source_pairs = []

        for ticker in tickers:
            for source in sources:
                if source == 'reddit':
                    tasks.append(self.fetch_reddit_sentiment(ticker))
                elif source == 'news':
                    tasks.append(self.fetch_news_sentiment(ticker))
                elif source == 'twitter':
                    tasks.append(self.fetch_twitter_sentiment(ticker))
                ticker_source_pairs.append((ticker, source))

        # 并发执行所有任务
        task_results = await asyncio.gather(*tasks, return_exceptions=True)

        # 整理结果
        for (ticker, source), result in zip(ticker_source_pairs, task_results):
            if ticker not in results:
                results[ticker] = {
                    'ticker': ticker,
                    'sources': {},
                    'aggregated_sentiment': None,
                    'timestamp': datetime.now().isoformat()
                }

            # 处理异常
            if isinstance(result, Exception):
                results[ticker]['sources'][source] = {
                    'source': source,
                    'ticker': ticker,
                    'error': str(result),
                    'timestamp': datetime.now().isoformat()
                }
            else:
                results[ticker]['sources'][source] = result

        # 计算聚合情绪分数
        for ticker_data in results.values():
            ticker_data['aggregated_sentiment'] = self._aggregate_sentiment(
                ticker_data['sources']
            )

        logger.info(f"情绪数据获取完成，共 {len(results)} 只股票")
        return results

    def _calculate_reddit_sentiment(self, data: List[Dict]) -> float:
        """
        计算 Reddit 情绪分数

        Args:
            data: Reddit 数据列表

        Returns:
            情绪分数 (0-1)
        """
        if not data:
            return 0.5

        total_score = 0
        total_weight = 0

        for post in data:
            # 使用评论数作为权重，假设有 sentiment 字段
            # 如果没有，使用 upvote_ratio 或默认中性
            comments = post.get('no_of_comments', 0) or 1
            sentiment = post.get('sentiment', 0.5)

            # 如果有 bullish/bearish 标记
            if post.get('sentiment') == 'Bullish':
                sentiment = 0.8
            elif post.get('sentiment') == 'Bearish':
                sentiment = 0.2

            total_score += sentiment * comments
            total_weight += comments

        return round(total_score / total_weight, 3) if total_weight > 0 else 0.5

    def _calculate_news_sentiment(self, data: Dict) -> float:
        """
        计算新闻情绪分数

        Args:
            data: NewsAPI 返回的数据

        Returns:
            情绪分数 (0-1)
        """
        articles = data.get('articles', [])
        if not articles:
            return 0.5

        # 简单实现：基于文章数量，实际应该使用 NLP 分析
        # 这里返回中性值，实际项目中应该集成情感分析模型
        total_articles = len(articles)

        # 可以基于标题关键词进行简单情绪判断
        positive_keywords = ['gain', 'rise', 'up', 'bull', 'positive', 'growth', 'profit']
        negative_keywords = ['loss', 'fall', 'down', 'bear', 'negative', 'decline', 'drop']

        positive_count = 0
        negative_count = 0

        for article in articles[:20]:  # 只分析前20篇
            title = article.get('title', '').lower()
            if any(kw in title for kw in positive_keywords):
                positive_count += 1
            if any(kw in title for kw in negative_keywords):
                negative_count += 1

        if positive_count + negative_count == 0:
            return 0.5

        return round(0.5 + (positive_count - negative_count) / (2 * (positive_count + negative_count)), 3)

    def _calculate_twitter_sentiment(self, data: Dict) -> float:
        """
        计算 Twitter 情绪分数

        Args:
            data: Twitter API 返回的数据

        Returns:
            情绪分数 (0-1)
        """
        tweets = data.get('data', [])
        if not tweets:
            return 0.5

        # 基于互动量加权
        total_engagement = 0
        total_weighted_sentiment = 0

        for tweet in tweets:
            metrics = tweet.get('public_metrics', {})
            engagement = (
                metrics.get('like_count', 0) +
                metrics.get('retweet_count', 0) * 2 +
                metrics.get('reply_count', 0)
            )

            # 简单实现：返回中性值
            # 实际项目中应该使用 NLP 进行情感分析
            total_weighted_sentiment += 0.5 * engagement
            total_engagement += engagement

        return round(total_weighted_sentiment / total_engagement, 3) if total_engagement > 0 else 0.5

    def _aggregate_sentiment(self, sources_data: Dict[str, Dict]) -> Dict[str, Any]:
        """
        聚合多个数据源的情绪分数

        Args:
            sources_data: 各数据源的情绪数据

        Returns:
            聚合后的情绪数据
        """
        valid_scores = []
        source_weights = {
            'reddit': 0.4,
            'twitter': 0.35,
            'news': 0.25
        }

        for source, data in sources_data.items():
            if 'sentiment_score' in data:
                weight = source_weights.get(source, 0.33)
                valid_scores.append((data['sentiment_score'], weight))

        if not valid_scores:
            return {
                'score': 0.5,
                'confidence': 0,
                'sources_used': 0
            }

        # 加权平均
        total_weight = sum(w for _, w in valid_scores)
        weighted_sum = sum(score * weight for score, weight in valid_scores)

        aggregated_score = weighted_sum / total_weight if total_weight > 0 else 0.5

        return {
            'score': round(aggregated_score, 3),
            'confidence': min(len(valid_scores) / 3, 1.0),  # 基于数据源数量的置信度
            'sources_used': len(valid_scores),
            'interpretation': self._interpret_sentiment(aggregated_score)
        }

    def _interpret_sentiment(self, score: float) -> str:
        """
        解释情绪分数

        Args:
            score: 情绪分数 (0-1)

        Returns:
            情绪解释
        """
        if score >= 0.7:
            return "非常看涨"
        elif score >= 0.6:
            return "看涨"
        elif score >= 0.55:
            return "轻微看涨"
        elif score >= 0.45:
            return "中性"
        elif score >= 0.4:
            return "轻微看跌"
        elif score >= 0.3:
            return "看跌"
        else:
            return "非常看跌"

    def clear_cache(self, ticker: Optional[str] = None, source: Optional[str] = None):
        """
        清除缓存

        Args:
            ticker: 股票代码，如果为 None 则清除所有
            source: 数据源，如果为 None 则清除所有
        """
        if ticker is None and source is None:
            self._cache.clear()
            logger.info("已清除所有情绪缓存")
        elif ticker is not None and source is not None:
            key = self._get_cache_key(source, ticker)
            if key in self._cache:
                del self._cache[key]
                logger.info(f"已清除缓存: {key}")
        else:
            # 按条件清除
            keys_to_remove = []
            for key in self._cache:
                parts = key.split(':')
                if len(parts) == 2:
                    key_source, key_ticker = parts
                    if (ticker and key_ticker == ticker) or (source and key_source == source):
                        keys_to_remove.append(key)

            for key in keys_to_remove:
                del self._cache[key]
            logger.info(f"已清除 {len(keys_to_remove)} 个缓存项")


class RealDataSources:
    """
    真实数据源管理器
    集成多个金融数据API
    """
    
    def __init__(self):
        """初始化数据源管理器"""
        # 从文档中提取的API密钥
        self.api_keys = {
            'fred': 'c917a48f98933615e6a208e7474b810c',  # FRED API
            'alpha_vantage': 'BBQTETM9CS8X8LI8',          # Alpha Vantage
            'fmp': 'oJw67iSq4FuJTIArmUKI9l3e3qZmNZod',    # Financial Modeling Prep
            'tradestie': None                            # Tradestie (无需密钥)
        }
        
        # API端点
        self.endpoints = {
            'fred': 'https://api.stlouisfed.org/fred',
            'alpha_vantage': 'https://www.alphavantage.co/query',
            'fmp': 'https://financialmodelingprep.com/api/v3',
            'tradestie': 'https://api.tradestie.com/v1/apps/reddit'
        }
        
        # 监控的股票列表
        self.watchlist = [
            '000001.SZ',  # 平安银行
            '600519.SS',  # 贵州茅台
            '601318.SS',  # 中国平安
            'AAPL',       # 苹果
            'MSFT',       # 微软
            'GOOGL',      # 谷歌
        ]
        
        logger.info("真实数据源管理器初始化完成")
        logger.info(f"已配置 {len(self.api_keys)} 个数据源API")
        
        # 初始化异步情绪分析器
        self._async_sentiment_analyzer: Optional[AsyncSentimentAnalyzer] = None
    
    def _get_async_sentiment_analyzer(self) -> AsyncSentimentAnalyzer:
        """
        获取异步情绪分析器实例（延迟初始化）
        
        Returns:
            AsyncSentimentAnalyzer 实例
        """
        if self._async_sentiment_analyzer is None:
            self._async_sentiment_analyzer = AsyncSentimentAnalyzer(
                news_api_key=self.api_keys.get('news_api'),
                twitter_bearer_token=self.api_keys.get('twitter')
            )
        return self._async_sentiment_analyzer
    
    async def get_sentiment_async(
        self,
        tickers: List[str],
        sources: Optional[List[str]] = None
    ) -> Dict[str, Dict[str, Any]]:
        """
        异步获取多个股票的情绪数据（入口方法）
        
        这是异步并发获取情绪数据的推荐方法，支持缓存和并发请求。
        
        Args:
            tickers: 股票代码列表
            sources: 数据源列表，可选 ['reddit', 'news', 'twitter']
                    如果为 None，则获取所有可用来源
        
        Returns:
            按股票代码分组的情绪数据，包含聚合情绪分数
        
        Example:
            >>> data_sources = RealDataSources()
            >>> # 在异步环境中
            >>> results = await data_sources.get_sentiment_async(
            ...     tickers=['AAPL', 'MSFT', 'GOOGL'],
            ...     sources=['reddit', 'news']
            ... )
            >>> for ticker, data in results.items():
            ...     print(f"{ticker}: {data['aggregated_sentiment']}")
        """
        analyzer = self._get_async_sentiment_analyzer()
        return await analyzer.async_fetch_sentiment(tickers, sources)
    
    def get_sentiment_sync(
        self,
        tickers: List[str],
        sources: Optional[List[str]] = None
    ) -> Dict[str, Dict[str, Any]]:
        """
        同步版本的获取情绪数据方法（向后兼容）
        
        这是同步包装器，内部使用异步实现。
        推荐在可能的情况下使用 get_sentiment_async()。
        
        Args:
            tickers: 股票代码列表
            sources: 数据源列表
        
        Returns:
            按股票代码分组的情绪数据
        """
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # 如果已经在异步环境中，创建新的线程运行
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(
                        asyncio.run,
                        self.get_sentiment_async(tickers, sources)
                    )
                    return future.result()
            else:
                return loop.run_until_complete(
                    self.get_sentiment_async(tickers, sources)
                )
        except RuntimeError:
            # 没有事件循环，创建新的
            return asyncio.run(self.get_sentiment_async(tickers, sources))
    
    async def close_async_resources(self):
        """
        关闭异步资源
        
        在使用完异步功能后调用此方法清理资源。
        """
        if self._async_sentiment_analyzer is not None:
            await self._async_sentiment_analyzer.close()
            self._async_sentiment_analyzer = None
    
    def get_fred_economic_data(self, series_id: str = 'GDP') -> Dict[str, Any]:
        """
        获取FRED经济数据
        
        Args:
            series_id: 数据系列ID
            
        Returns:
            经济数据
        """
        try:
            url = f"{self.endpoints['fred']}/series/observations"
            params = {
                'series_id': series_id,
                'api_key': self.api_keys['fred'],
                'file_type': 'json'
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"成功获取FRED数据: {series_id}")
                return {
                    'source': 'fred',
                    'series_id': series_id,
                    'data': data.get('observations', []),
                    'timestamp': datetime.now().isoformat()
                }
            else:
                logger.error(f"FRED API错误: {response.status_code}")
                return {'error': f"API错误: {response.status_code}"}
                
        except Exception as e:
            logger.error(f"获取FRED数据时出错: {e}")
            return {'error': str(e)}
    
    def get_alpha_vantage_stock_data(self, symbol: str) -> Dict[str, Any]:
        """
        获取Alpha Vantage股票数据
        
        Args:
            symbol: 股票代码
            
        Returns:
            股票数据
        """
        try:
            params = {
                'function': 'TIME_SERIES_DAILY',
                'symbol': symbol,
                'apikey': self.api_keys['alpha_vantage'],
                'outputsize': 'compact'  # 最近100个数据点
            }
            
            response = requests.get(self.endpoints['alpha_vantage'], params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                # 检查是否有错误信息
                if 'Error Message' in data:
                    logger.error(f"Alpha Vantage错误: {data['Error Message']}")
                    return {'error': data['Error Message']}
                
                logger.info(f"成功获取Alpha Vantage数据: {symbol}")
                return {
                    'source': 'alpha_vantage',
                    'symbol': symbol,
                    'data': data.get('Time Series (Daily)', {}),
                    'metadata': data.get('Meta Data', {}),
                    'timestamp': datetime.now().isoformat()
                }
            else:
                logger.error(f"Alpha Vantage API错误: {response.status_code}")
                return {'error': f"API错误: {response.status_code}"}
                
        except Exception as e:
            logger.error(f"获取Alpha Vantage数据时出错: {e}")
            return {'error': str(e)}
    
    def get_fmp_financial_data(self, symbol: str) -> Dict[str, Any]:
        """
        获取Financial Modeling Prep财务数据
        
        Args:
            symbol: 股票代码
            
        Returns:
            财务数据
        """
        try:
            # 获取公司简介
            profile_url = f"{self.endpoints['fmp']}/profile/{symbol}"
            profile_params = {'apikey': self.api_keys['fmp']}
            
            # 获取财务比率
            ratios_url = f"{self.endpoints['fmp']}/ratios/{symbol}"
            ratios_params = {'apikey': self.api_keys['fmp']}
            
            profile_response = requests.get(profile_url, params=profile_params, timeout=10)
            ratios_response = requests.get(ratios_url, params=ratios_params, timeout=10)
            
            profile_data = profile_response.json() if profile_response.status_code == 200 else []
            ratios_data = ratios_response.json() if ratios_response.status_code == 200 else []
            
            logger.info(f"成功获取FMP数据: {symbol}")
            return {
                'source': 'fmp',
                'symbol': symbol,
                'profile': profile_data[0] if profile_data else {},
                'ratios': ratios_data[0] if ratios_data else {},
                'timestamp': datetime.now().isoformat()
            }
                
        except Exception as e:
            logger.error(f"获取FMP数据时出错: {e}")
            return {'error': str(e)}
    
    def get_reddit_sentiment_data(self, ticker: str = 'GME') -> Dict[str, Any]:
        """
        获取Reddit市场情绪数据
        
        Args:
            ticker: 股票代码
            
        Returns:
            Reddit情绪数据
        """
        try:
            url = self.endpoints['tradestie']
            params = {'ticker': ticker}
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"成功获取Reddit情绪数据: {ticker}")
                return {
                    'source': 'tradestie',
                    'ticker': ticker,
                    'data': data,
                    'timestamp': datetime.now().isoformat()
                }
            else:
                logger.error(f"Tradestie API错误: {response.status_code}")
                return {'error': f"API错误: {response.status_code}"}
                
        except Exception as e:
            logger.error(f"获取Reddit情绪数据时出错: {e}")
            return {'error': str(e)}
    
    def get_comprehensive_market_data(self, symbol: str) -> Dict[str, Any]:
        """
        获取综合市场数据（多数据源）
        
        Args:
            symbol: 股票代码
            
        Returns:
            综合市场数据
        """
        logger.info(f"开始获取综合市场数据: {symbol}")
        
        comprehensive_data = {
            'symbol': symbol,
            'timestamp': datetime.now().isoformat(),
            'sources': {},
            'summary': {}
        }
        
        # 1. 获取股票价格数据（Alpha Vantage）
        stock_data = self.get_alpha_vantage_stock_data(symbol)
        if 'error' not in stock_data:
            comprehensive_data['sources']['alpha_vantage'] = stock_data
            
            # 提取最新价格信息
            if 'data' in stock_data and stock_data['data']:
                latest_date = max(stock_data['data'].keys())
                latest_data = stock_data['data'][latest_date]
                
                comprehensive_data['summary']['price'] = {
                    'date': latest_date,
                    'open': float(latest_data.get('1. open', 0)),
                    'high': float(latest_data.get('2. high', 0)),
                    'low': float(latest_data.get('3. low', 0)),
                    'close': float(latest_data.get('4. close', 0)),
                    'volume': int(latest_data.get('5. volume', 0))
                }
        
        # 2. 获取财务数据（FMP）
        financial_data = self.get_fmp_financial_data(symbol)
        if 'error' not in financial_data:
            comprehensive_data['sources']['fmp'] = financial_data
            
            # 提取关键财务指标
            if 'profile' in financial_data:
                comprehensive_data['summary']['company'] = {
                    'name': financial_data['profile'].get('companyName', ''),
                    'sector': financial_data['profile'].get('sector', ''),
                    'industry': financial_data['profile'].get('industry', ''),
                    'market_cap': financial_data['profile'].get('mktCap', 0)
                }
        
        # 3. 获取市场情绪数据（Reddit）
        if len(symbol) <= 4:  # 只对美股获取Reddit数据
            sentiment_data = self.get_reddit_sentiment_data(symbol)
            if 'error' not in sentiment_data:
                comprehensive_data['sources']['reddit'] = sentiment_data
                
                # 提取情绪指标
                if 'data' in sentiment_data and sentiment_data['data']:
                    comprehensive_data['summary']['sentiment'] = {
                        'mentions': len(sentiment_data['data']),
                        'sentiment_score': self._calculate_sentiment_score(sentiment_data['data'])
                    }
        
        # 4. 获取宏观经济数据（FRED）
        gdp_data = self.get_fred_economic_data('GDP')
        if 'error' not in gdp_data:
            comprehensive_data['sources']['fred'] = gdp_data
        
        logger.info(f"综合市场数据获取完成: {symbol}")
        return comprehensive_data
    
    def _calculate_sentiment_score(self, reddit_data: List[Dict]) -> float:
        """计算Reddit情绪分数"""
        if not reddit_data:
            return 0.5  # 中性
        
        total_score = 0
        count = 0
        
        for post in reddit_data:
            # 这里可以根据实际数据结构调整
            # 假设每个帖子有一个sentiment字段
            sentiment = post.get('sentiment', 0.5)
            total_score += sentiment
            count += 1
        
        return round(total_score / count, 3) if count > 0 else 0.5
    
    def collect_all_watchlist_data(self) -> Dict[str, Any]:
        """
        收集所有监控股票的数据
        
        Returns:
            所有股票的数据
        """
        logger.info(f"开始收集监控列表数据，共{len(self.watchlist)}只股票")
        
        all_data = {
            'timestamp': datetime.now().isoformat(),
            'stocks': {},
            'statistics': {
                'total_stocks': len(self.watchlist),
                'successful_collections': 0,
                'failed_collections': 0
            }
        }
        
        for symbol in self.watchlist:
            try:
                stock_data = self.get_comprehensive_market_data(symbol)
                all_data['stocks'][symbol] = stock_data
                
                if 'error' not in stock_data:
                    all_data['statistics']['successful_collections'] += 1
                else:
                    all_data['statistics']['failed_collections'] += 1
                    logger.warning(f"收集{symbol}数据时出错: {stock_data.get('error')}")
                    
            except Exception as e:
                all_data['statistics']['failed_collections'] += 1
                logger.error(f"处理{symbol}时异常: {e}")
        
        logger.info(f"数据收集完成: {all_data['statistics']}")
        return all_data
    
    def save_data_to_file(self, data: Dict[str, Any], filename: str = None):
        """
        保存数据到文件
        
        Args:
            data: 要保存的数据
            filename: 文件名（可选）
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"market_data_{timestamp}.json"
        
        data_dir = Path("real_market_data")
        data_dir.mkdir(exist_ok=True)
        
        filepath = data_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"数据已保存到: {filepath}")
        return str(filepath)


# 测试函数
def test_real_data_sources():
    """测试真实数据源"""
    import logging
    
    logging.basicConfig(level=logging.INFO)
    
    print("🧪 测试真实数据源集成")
    print("=" * 60)
    
    data_sources = RealDataSources()
    
    # 测试单个股票数据
    print("\n1. 测试单个股票综合数据 (AAPL):")
    apple_data = data_sources.get_comprehensive_market_data('AAPL')
    
    if 'summary' in apple_data:
        summary = apple_data['summary']
        print(f"   价格数据: {summary.get('price', {}).get('close', 'N/A')}")
        print(f"   公司信息: {summary.get('company', {}).get('name', 'N/A')}")
        print(f"   情绪分数: {summary.get('sentiment', {}).get('sentiment_score', 'N/A')}")
        print(f"   数据来源: {', '.join(apple_data['sources'].keys())}")
    else:
        print(f"   错误: {apple_data.get('error', '未知错误')}")
    
    # 测试A股数据
    print("\n2. 测试A股数据 (平安银行):")
    # 注意：Alpha Vantage可能不支持A股，使用本地数据源
    from data.acquisition.cn_market import CNMarketDataFetcher
    cn_fetcher = CNMarketDataFetcher(prefered_lib="tushare")
    cn_data = cn_fetcher.get_stock_quote('000001')
    print(f"   股票: {cn_data.get('name', 'N/A')}")
    print(f"   价格: {cn_data.get('price', 'N/A')}")
    print(f"   涨跌幅: {cn_data.get('change_percent', 'N/A')}%")
    
    # 收集所有监控股票数据
    print("\n3. 收集所有监控股票数据:")
    all_data = data_sources.collect_all_watchlist_data()
    stats = all_data['statistics']
    print(f"   成功: {stats['successful_collections']}")
    print(f"   失败: {stats['failed_collections']}")
    
    # 保存数据
    print("\n4. 保存数据到文件:")
    saved_file = data_sources.save_data_to_file(all_data)
    print(f"   数据已保存到: {saved_file}")
    
    print("\n🎯 真实数据源测试完成!")
    print("\n📊 可用数据源总结:")
    print("   • FRED - 宏观经济数据")
    print("   • Alpha Vantage - 全球股票价格数据")
    print("   • Financial Modeling Prep - 财务数据")
    print("   • Tradestie - Reddit市场情绪数据")
    print("   • Tushare - 中国A股实时数据")


async def test_async_sentiment_analyzer():
    """测试异步情绪分析功能"""
    import logging

    logging.basicConfig(level=logging.INFO)

    print("\n🧪 测试异步情绪分析功能")
    print("=" * 60)

    # 创建异步分析器实例
    analyzer = AsyncSentimentAnalyzer(
        news_api_key=None,  # 可以配置 NewsAPI 密钥
        twitter_bearer_token=None,  # 可以配置 Twitter Bearer Token
        cache_ttl=300  # 5分钟缓存
    )

    try:
        # 测试 1: 单个股票的 Reddit 情绪
        print("\n1. 测试 Reddit 情绪获取 (AAPL):")
        reddit_data = await analyzer.fetch_reddit_sentiment('AAPL')
        if 'error' not in reddit_data:
            print(f"   情绪分数: {reddit_data.get('sentiment_score', 'N/A')}")
            print(f"   数据条目: {len(reddit_data.get('data', []))}")
        else:
            print(f"   错误: {reddit_data.get('error')}")

        # 测试 2: 并发获取多个股票的情绪数据
        print("\n2. 测试并发获取多股票情绪:")
        tickers = ['AAPL', 'MSFT', 'GOOGL', 'TSLA']

        import time
        start_time = time.time()
        results = await analyzer.async_fetch_sentiment(
            tickers=tickers,
            sources=['reddit']  # 只使用 Reddit（免费无需认证）
        )
        elapsed = time.time() - start_time

        print(f"   耗时: {elapsed:.2f}秒")
        for ticker, data in results.items():
            agg = data.get('aggregated_sentiment', {})
            print(f"   {ticker}: 分数={agg.get('score', 'N/A')}, "
                  f"解读={agg.get('interpretation', 'N/A')}")

        # 测试 3: 缓存机制
        print("\n3. 测试缓存机制:")
        print("   再次请求相同数据（应该命中缓存）...")
        start_time = time.time()
        cached_results = await analyzer.async_fetch_sentiment(
            tickers=['AAPL'],
            sources=['reddit']
        )
        cache_elapsed = time.time() - start_time
        print(f"   缓存命中耗时: {cache_elapsed:.4f}秒")
        print(f"   (对比首次请求: {elapsed:.2f}秒)")

        # 测试 4: 通过 RealDataSources 入口
        print("\n4. 测试 RealDataSources 异步入口:")
        data_sources = RealDataSources()
        sentiment_data = await data_sources.get_sentiment_async(
            tickers=['NVDA', 'AMD'],
            sources=['reddit']
        )
        for ticker, data in sentiment_data.items():
            agg = data.get('aggregated_sentiment', {})
            print(f"   {ticker}: {agg.get('interpretation', 'N/A')} "
                  f"(置信度: {agg.get('confidence', 0):.0%})")

        # 清理资源
        await data_sources.close_async_resources()

    finally:
        # 关闭 aiohttp session
        await analyzer.close()

    print("\n🎯 异步情绪分析测试完成!")
    print("\n📋 功能总结:")
    print("   ✅ AsyncSentimentAnalyzer 类 - 使用 asyncio 和 aiohttp")
    print("   ✅ 并发获取多数据源情绪数据 (Reddit/News/Twitter)")
    print("   ✅ async_fetch_sentiment() - 并发获取多股票情绪")
    print("   ✅ 缓存机制 - TTL 5分钟，LRU 淘汰")
    print("   ✅ get_sentiment_async() - RealDataSources 入口方法")
    print("   ✅ 向后兼容 - 原有同步方法继续可用")


def test_sync_sentiment():
    """测试同步包装器（向后兼容）"""
    print("\n🧪 测试同步情绪获取方法")
    print("=" * 60)

    data_sources = RealDataSources()

    # 使用同步方法（内部调用异步实现）
    print("\n使用同步方法获取情绪数据:")
    results = data_sources.get_sentiment_sync(
        tickers=['AAPL', 'MSFT'],
        sources=['reddit']
    )

    for ticker, data in results.items():
        agg = data.get('aggregated_sentiment', {})
        print(f"   {ticker}: {agg.get('interpretation', 'N/A')}")

    print("\n✅ 同步方法测试完成!")


if __name__ == "__main__":
    # 测试原有功能
    test_real_data_sources()

    # 测试异步功能
    print("\n" + "=" * 60)
    asyncio.run(test_async_sentiment_analyzer())

    # 测试同步包装器
    print("\n" + "=" * 60)
    test_sync_sentiment()