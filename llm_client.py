#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LLM 客户端 - 统一接口
支持 DeepSeek, OpenAI, Kimi 等

基于 Vibe Coding 方法论

运行方式:
    python llm_client.py --prompt "你好"
    python llm_client.py --test
"""

import os
import json
import requests
from typing import Optional, List, Dict
from dataclasses import dataclass
from datetime import datetime

# DeepSeek API 配置 (来自 OpenClaw)
DEEPSEEK_CONFIG = {
    "base_url": "https://api.deepseek.com/v1",
    "api_key": "sk-55369c09b7fb482096e8069e6794e4a1",
    "model": "deepseek-chat"
}


@dataclass
class Message:
    """对话消息"""
    role: str  # system, user, assistant
    content: str


class LLMClient:
    """LLM 统一客户端"""
    
    def __init__(self, provider: str = "deepseek"):
        self.provider = provider
        self.config = DEEPSEEK_CONFIG
        self.conversation_history: List[Message] = []
    
    def chat(self, prompt: str, system_prompt: str = None, 
             temperature: float = 0.7, max_tokens: int = 2048) -> str:
        """
        发送对话请求
        
        Args:
            prompt: 用户输入
            system_prompt: 系统提示词
            temperature: 温度参数
            max_tokens: 最大生成 token 数
        
        Returns:
            模型回复
        """
        messages = []
        
        # 添加系统提示
        if system_prompt:
            messages.append({
                "role": "system",
                "content": system_prompt
            })
        
        # 添加历史对话
        for msg in self.conversation_history:
            messages.append({
                "role": msg.role,
                "content": msg.content
            })
        
        # 添加当前输入
        messages.append({
            "role": "user",
            "content": prompt
        })
        
        # 调用 API
        if self.provider == "deepseek":
            return self._call_deepseek(messages, temperature, max_tokens)
        else:
            raise ValueError(f"不支持的 provider: {self.provider}")
    
    def _call_deepseek(self, messages: List[Dict], 
                      temperature: float, max_tokens: int) -> str:
        """调用 DeepSeek API"""
        url = f"{self.config['base_url']}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.config['api_key']}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": self.config["model"],
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        try:
            response = requests.post(url, headers=headers, json=data, timeout=60)
            response.raise_for_status()
            
            result = response.json()
            content = result["choices"][0]["message"]["content"]
            
            # 保存到历史
            self.conversation_history.append(Message("user", messages[-1]["content"]))
            self.conversation_history.append(Message("assistant", content))
            
            return content
            
        except requests.exceptions.Timeout:
            return "❌ 请求超时，请重试"
        except requests.exceptions.RequestException as e:
            return f"❌ 请求失败: {str(e)}"
        except KeyError as e:
            return f"❌ 响应解析失败: {str(e)}"
    
    def clear_history(self):
        """清空对话历史"""
        self.conversation_history = []
    
    def stock_analysis_prompt(self, symbol: str, price_data: Dict) -> str:
        """
        股票分析提示词
        
        Args:
            symbol: 股票代码
            price_data: 股价数据
        
        Returns:
            分析结果
        """
        system_prompt = """你是一个专业的股票分析师助手。
请基于提供的市场数据，给出简洁专业的分析意见。
分析维度：
1. 价格走势 (短期/中期)
2. 技术指标信号
3. 成交量分析
4. 风险提示
5. 建议 (买入/持有/卖出)

注意：只做分析建议，不构成投资决策。"""
        
        prompt = f"""请分析股票 {symbol}：

当前价格数据：
{json.dumps(price_data, ensure_ascii=False, indent=2)}

请给出分析意见。"""
        
        return self.chat(prompt, system_prompt)


def test():
    """测试 LLM 客户端"""
    print("🧪 测试 LLM 客户端...")
    print("=" * 50)
    
    client = LLMClient("deepseek")
    
    # 简单测试
    print("\n📌 测试 1: 简单对话")
    response = client.chat("你好，请用一句话介绍自己")
    print(f"  回复: {response[:100]}...")
    
    # 股票分析测试
    print("\n📌 测试 2: 股票分析")
    sample_data = {
        "symbol": "000001",
        "name": "平安银行",
        "price": 10.91,
        "change": -0.46,
        "volume": 55504736,
        "high_5d": 11.10,
        "low_5d": 10.77
    }
    response = client.stock_analysis_prompt("000001", sample_data)
    print(f"  分析: {response[:200]}...")
    
    print("\n" + "=" * 50)
    print("✅ 测试完成!")
    
    client.clear_history()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='LLM 客户端')
    parser.add_argument('--prompt', type=str, help='输入提示词')
    parser.add_argument('--system', type=str, help='系统提示词')
    parser.add_argument('--test', action='store_true', help='运行测试')
    parser.add_argument('--clear', action='store_true', help='清空对话历史')
    
    args = parser.parse_args()
    
    client = LLMClient("deepseek")
    
    if args.test:
        test()
    elif args.clear:
        client.clear_history()
        print("✅ 对话历史已清空")
    elif args.prompt:
        response = client.chat(args.prompt, args.system)
        print(response)
    else:
        # 交互模式
        print("🎙️ LLM 交互模式 (输入 'quit' 退出)")
        print("=" * 50)
        
        while True:
            try:
                prompt = input("\n👤 你: ")
                if prompt.lower() in ['quit', 'exit', 'q']:
                    break
                
                response = client.chat(prompt)
                print(f"\n🤖 AI: {response}")
                
            except KeyboardInterrupt:
                break
        
        print("\n👋 再见!")


# ========== Agent 框架基础 ==========

class BaseAgent:
    """Agent 基类"""
    
    def __init__(self, name: str, llm_client: LLMClient):
        self.name = name
        self.llm = llm_client
    
    def analyze(self, data: Dict) -> str:
        """分析数据"""
        raise NotImplementedError
    
    def run(self, data: Dict) -> Dict:
        """运行 Agent"""
        result = self.analyze(data)
        return {
            "agent": self.name,
            "result": result,
            "timestamp": datetime.now().isoformat()
        }


class ValuationAgent(BaseAgent):
    """估值 Agent"""
    
    def analyze(self, data: Dict) -> str:
        prompt = f"""作为估值分析师，请分析以下股票的估值水平：

股票: {data.get('name', '')} ({data.get('symbol', '')})
当前价格: ¥{data.get('price', 0)}
市净率(PB): {data.get('pb', 'N/A')}
市盈率(PE): {data.get('pe', 'N/A')}

请给出估值判断："""
        return self.llm.chat(prompt)


class TechnicalAgent(BaseAgent):
    """技术分析 Agent"""
    
    def analyze(self, data: Dict) -> str:
        prompt = f"""作为技术分析师，请分析以下股票的技术走势：

股票: {data.get('name', '')} ({data.get('symbol', '')})
当前价格: ¥{data.get('price', 0)}
5日涨跌: {data.get('change_5d', 0):+.2f}%
成交量: {data.get('volume', 0):,}

请给出技术分析："""
        return self.llm.chat(prompt)


class SentimentAgent(BaseAgent):
    """情绪分析 Agent"""
    
    def analyze(self, data: Dict) -> str:
        prompt = f"""作为情绪分析师，请分析以下股票的市场情绪：

股票: {data.get('name', '')} ({data.get('symbol', '')})
近期涨跌幅: {data.get('change_1d', 0):+.2f}%
成交量变化: {data.get('volume_change', 0):+.1f}%

请给出情绪判断："""
        return self.llm.chat(prompt)


class PortfolioManagerAgent(BaseAgent):
    """组合管理 Agent - 汇总决策"""
    
    def __init__(self, name: str, llm_client: LLMClient):
        super().__init__(name, llm_client)
        self.agents = []
    
    def add_agent(self, agent: BaseAgent):
        """添加分析 Agent"""
        self.agents.append(agent)
    
    def analyze(self, data: Dict) -> str:
        # 先运行所有子 Agent
        results = []
        for agent in self.agents:
            result = agent.run(data)
            results.append(f"【{agent.name}】\n{result['result']}")
        
        # 汇总分析
        combined = "\n\n".join(results)
        prompt = f"""作为投资组合经理，请综合以下分析给出最终建议：

{combined}

请给出：
1. 综合判断
2. 建议仓位
3. 风险提示

注意：仅供研究参考，不构成投资建议。"""
        
        return self.llm.chat(prompt)


if __name__ == "__main__":
    # 演示 Agent 使用
    print("=" * 60)
    print("🎯 DSS AI Agent 系统演示")
    print("=" * 60)
    
    llm = LLMClient("deepseek")
    
    # 示例数据
    stock_data = {
        "symbol": "000001",
        "name": "平安银行",
        "price": 10.91,
        "change_1d": -0.46,
        "change_5d": -1.72,
        "volume": 55504736,
        "volume_change": 28.8,
        "pe": 4.5,
        "pb": 0.45
    }
    
    # 创建 Agent 组合
    pm = PortfolioManagerAgent("投资组合经理", llm)
    pm.add_agent(ValuationAgent("估值分析", llm))
    pm.add_agent(TechnicalAgent("技术分析", llm))
    pm.add_agent(SentimentAgent("情绪分析", llm))
    
    print(f"\n📊 分析股票: {stock_data['name']} ({stock_data['symbol']})")
    print("-" * 60)
    
    # 运行分析
    result = pm.run(stock_data)
    print(result['result'])
