"""
Market Analysis Agent - Analyzes real-time market data and generates trading signals
"""
import json
import pandas as pd
import pandas_ta as ta
from typing import Dict, Any, List, Optional
from alpaca.data.live import StockDataStream
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from alpaca.data.historical import StockHistoricalDataClient
from datetime import datetime, timedelta
from .base_agent import BaseAgent


class MarketAgent(BaseAgent):
    """Agent responsible for market analysis and signal generation"""
    
    def __init__(self, alpaca_api_key: str, alpaca_secret_key: str):
        super().__init__(
            name="market_agent",
            instruction="""You are a sophisticated market analysis agent. Your role is to:
            1. Analyze real-time market data and technical indicators
            2. Identify trading opportunities based on technical analysis
            3. Generate clear buy/sell signals with confidence levels
            4. Provide detailed analysis reasoning
            5. Communicate findings to other agents via A2A protocol
            
            Always provide structured responses with clear recommendations."""
        )
        
        self.alpaca_api_key = alpaca_api_key
        self.alpaca_secret_key = alpaca_secret_key
        # Use IEX data for paper trading (free tier)
        self.historical_client = StockHistoricalDataClient(alpaca_api_key, alpaca_secret_key, url_override="https://data.alpaca.markets")
        self.data_stream = StockDataStream(alpaca_api_key, alpaca_secret_key)
        self.watchlist = ["AAPL", "GOOGL", "MSFT", "TSLA", "NVDA"]
        
    async def analyze_stock(self, symbol: str, timeframe: str = "1Hour") -> Dict[str, Any]:
        """Analyze a single stock and generate trading signal"""
        try:
            # Get historical data - use longer timeframe for paper trading
            end_date = datetime.now() - timedelta(days=2)  # Avoid recent data restrictions
            start_date = end_date - timedelta(days=60)  # More history for better indicators
            
            request = StockBarsRequest(
                symbol_or_symbols=symbol,
                timeframe=TimeFrame.Day,  # Use daily data for paper trading
                start=start_date,
                end=end_date
            )
            
            bars = self.historical_client.get_stock_bars(request)
            df = bars.df
            
            if df.empty:
                return {"error": f"No data available for {symbol}"}
            
            # Calculate technical indicators
            df['rsi'] = ta.rsi(df['close'], length=14)
            df['macd'] = ta.macd(df['close'])['MACD_12_26_9']
            df['sma_20'] = ta.sma(df['close'], length=20)
            df['sma_50'] = ta.sma(df['close'], length=50)
            bb_result = ta.bbands(df['close'], length=20)
            df['bb_upper'] = bb_result.iloc[:, 0]  # Upper band
            df['bb_middle'] = bb_result.iloc[:, 1]  # Middle band  
            df['bb_lower'] = bb_result.iloc[:, 2]  # Lower band
            
            # Get latest values
            latest = df.iloc[-1]
            
            # Create analysis context
            analysis_data = {
                "symbol": symbol,
                "price": float(latest['close']),
                "volume": int(latest['volume']),
                "rsi": float(latest['rsi']) if pd.notna(latest['rsi']) else None,
                "macd": float(latest['macd']) if pd.notna(latest['macd']) else None,
                "sma_20": float(latest['sma_20']) if pd.notna(latest['sma_20']) else None,
                "sma_50": float(latest['sma_50']) if pd.notna(latest['sma_50']) else None,
                "bb_upper": float(latest['bb_upper']) if pd.notna(latest['bb_upper']) else None,
                "bb_lower": float(latest['bb_lower']) if pd.notna(latest['bb_lower']) else None,
                "price_change": float(latest['close'] - df.iloc[-2]['close']),
                "price_change_pct": float((latest['close'] - df.iloc[-2]['close']) / df.iloc[-2]['close'] * 100)
            }
            
            # Generate AI analysis
            rsi_str = f"{analysis_data['rsi']:.2f}" if analysis_data['rsi'] else 'N/A'
            macd_str = f"{analysis_data['macd']:.4f}" if analysis_data['macd'] else 'N/A'
            sma_20_str = f"${analysis_data['sma_20']:.2f}" if analysis_data['sma_20'] else 'N/A'
            sma_50_str = f"${analysis_data['sma_50']:.2f}" if analysis_data['sma_50'] else 'N/A'
            bb_upper_str = f"${analysis_data['bb_upper']:.2f}" if analysis_data['bb_upper'] else 'N/A'
            bb_lower_str = f"${analysis_data['bb_lower']:.2f}" if analysis_data['bb_lower'] else 'N/A'
            
            analysis_prompt = f"""
            Analyze the following market data for {symbol} and provide a trading recommendation:
            
            Current Price: ${analysis_data['price']:.2f}
            Price Change: ${analysis_data['price_change']:.2f} ({analysis_data['price_change_pct']:.2f}%)
            Volume: {analysis_data['volume']:,}
            RSI: {rsi_str}
            MACD: {macd_str}
            SMA 20: {sma_20_str}
            SMA 50: {sma_50_str}
            Bollinger Upper: {bb_upper_str}
            Bollinger Lower: {bb_lower_str}
            
            Provide your analysis in the following JSON format:
            {{
                "signal": "BUY|SELL|HOLD",
                "confidence": 0.0-1.0,
                "reasoning": "detailed explanation",
                "target_price": "price target if applicable",
                "stop_loss": "stop loss level if applicable",
                "risk_level": "LOW|MEDIUM|HIGH"
            }}
            """
            
            ai_response = await self.process_message(analysis_prompt)
            
            # Try to extract JSON from response
            try:
                # Find JSON in the response
                start_idx = ai_response.find('{')
                end_idx = ai_response.rfind('}') + 1
                if start_idx != -1 and end_idx != -1:
                    json_str = ai_response[start_idx:end_idx]
                    ai_analysis = json.loads(json_str)
                else:
                    ai_analysis = {"signal": "HOLD", "confidence": 0.5, "reasoning": ai_response}
            except:
                ai_analysis = {"signal": "HOLD", "confidence": 0.5, "reasoning": ai_response}
            
            # Combine technical and AI analysis
            result = {
                "symbol": symbol,
                "timestamp": datetime.now().isoformat(),
                "market_data": analysis_data,
                "ai_analysis": ai_analysis,
                "technical_summary": self._generate_technical_summary(analysis_data)
            }
            
            return result
            
        except Exception as e:
            return {"error": str(e), "symbol": symbol}
    
    def _generate_technical_summary(self, data: Dict[str, Any]) -> Dict[str, str]:
        """Generate technical analysis summary"""
        summary = {}
        
        # RSI Analysis
        if data['rsi']:
            if data['rsi'] > 70:
                summary['rsi'] = "Overbought"
            elif data['rsi'] < 30:
                summary['rsi'] = "Oversold"
            else:
                summary['rsi'] = "Neutral"
        
        # Moving Average Analysis
        if data['sma_20'] and data['sma_50']:
            if data['sma_20'] > data['sma_50']:
                summary['trend'] = "Bullish"
            else:
                summary['trend'] = "Bearish"
        
        # Bollinger Bands Analysis
        if data['bb_upper'] and data['bb_lower']:
            if data['price'] > data['bb_upper']:
                summary['bb_position'] = "Above Upper Band"
            elif data['price'] < data['bb_lower']:
                summary['bb_position'] = "Below Lower Band"
            else:
                summary['bb_position'] = "Within Bands"
        
        return summary
    
    async def scan_watchlist(self) -> List[Dict[str, Any]]:
        """Scan all watchlist symbols and return analysis"""
        results = []
        for symbol in self.watchlist:
            analysis = await self.analyze_stock(symbol)
            results.append(analysis)
        return results
    
    def _get_specific_capabilities(self) -> Dict[str, Any]:
        """Define Market Agent specific capabilities"""
        return {
            "functions": [
                "analyze_stock",
                "scan_watchlist",
                "generate_trading_signals",
                "technical_analysis"
            ],
            "data_sources": [
                "alpaca_markets",
                "real_time_quotes",
                "historical_data"
            ],
            "indicators": [
                "RSI",
                "MACD", 
                "Moving_Averages",
                "Bollinger_Bands"
            ]
        }