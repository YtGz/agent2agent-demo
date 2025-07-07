"""
Main entry point for the Multi-Agent Trading Demo
"""
import os
import asyncio
from dotenv import load_dotenv
from agents.market_agent import MarketAgent

load_dotenv()


async def main():
    """Main demo function"""
    print("🚀 Multi-Agent Trading Demo Starting...")
    print("=" * 50)
    
    # Initialize agents
    try:
        alpaca_api_key = os.getenv("ALPACA_API_KEY")
        alpaca_secret_key = os.getenv("ALPACA_SECRET_KEY")
        
        if not alpaca_api_key or not alpaca_secret_key:
            print("❌ Please set ALPACA_API_KEY and ALPACA_SECRET_KEY in .env file")
            return
        
        # Create Market Agent
        print("📊 Initializing Market Analysis Agent...")
        market_agent = MarketAgent(alpaca_api_key, alpaca_secret_key)
        
        # Test market analysis
        print("\n🔍 Analyzing AAPL...")
        analysis = await market_agent.analyze_stock("AAPL")
        
        if "error" in analysis:
            print(f"❌ Error: {analysis['error']}")
        else:
            print(f"✅ Analysis complete for {analysis['symbol']}")
            print(f"📈 Current Price: ${analysis['market_data']['price']:.2f}")
            print(f"📊 Signal: {analysis['ai_analysis'].get('signal', 'N/A')}")
            print(f"🎯 Confidence: {analysis['ai_analysis'].get('confidence', 0):.2f}")
            print(f"💭 Reasoning: {analysis['ai_analysis'].get('reasoning', 'N/A')}")
        
        print("\n🔍 Scanning watchlist...")
        watchlist_results = await market_agent.scan_watchlist()
        
        print("\n📋 Watchlist Summary:")
        for result in watchlist_results:
            if "error" not in result:
                symbol = result['symbol']
                signal = result['ai_analysis'].get('signal', 'HOLD')
                price = result['market_data']['price']
                print(f"  {symbol}: {signal} @ ${price:.2f}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())