"""
Test script to demonstrate execution with a mock BUY signal
"""
import os
import asyncio
from dotenv import load_dotenv
from agents.agent_coordinator import AgentCoordinator

load_dotenv()


async def test_execution_demo():
    """Test execution with a forced BUY signal"""
    print("🧪 Testing Execution Agent with Mock BUY Signal")
    print("=" * 60)
    
    alpaca_api_key = os.getenv("ALPACA_API_KEY")
    alpaca_secret_key = os.getenv("ALPACA_SECRET_KEY")
    
    if not alpaca_api_key or not alpaca_secret_key:
        print("❌ Please set ALPACA_API_KEY and ALPACA_SECRET_KEY in .env file")
        return
    
    coordinator = AgentCoordinator(alpaca_api_key, alpaca_secret_key)
    
    # Create a mock trade signal that will likely be approved
    mock_market_analysis = {
        "symbol": "AAPL",
        "timestamp": "2024-01-07T00:00:00",
        "market_data": {
            "symbol": "AAPL",
            "price": 213.55,
            "volume": 50000000,
            "rsi": 45.0,  # Neutral RSI
            "macd": 0.5,  # Positive MACD
            "sma_20": 210.0,
            "sma_50": 205.0,
            "bb_upper": 220.0,
            "bb_lower": 200.0,
            "price_change": 2.5,
            "price_change_pct": 1.2
        },
        "ai_analysis": {
            "signal": "BUY",  # Force a BUY signal
            "confidence": 0.75,  # High confidence
            "reasoning": "Strong technical indicators with neutral RSI and positive momentum",
            "target_price": "220.00",
            "stop_loss": "200.00", 
            "risk_level": "LOW"
        },
        "technical_summary": {
            "rsi": "Neutral",
            "trend": "Bullish",
            "bb_position": "Within Bands"
        }
    }
    
    print("📊 Using Mock Market Analysis:")
    print(f"   Symbol: AAPL")
    print(f"   Signal: BUY")
    print(f"   Confidence: 0.75")
    print(f"   Price: $213.55")
    
    print("\n🛡️  Risk Agent evaluating mock signal...")
    risk_evaluation = await coordinator.risk_agent.evaluate_trade_signal(mock_market_analysis)
    
    if "error" in risk_evaluation:
        print(f"❌ Risk evaluation failed: {risk_evaluation['error']}")
        return
    
    print("🔄 A2A Communication: market_agent → risk_agent → execution_agent")
    
    decision = risk_evaluation.get("decision", {})
    print(f"\n🛡️  Risk Decision:")
    print(f"   Action: {decision.get('action', 'N/A')}")
    print(f"   Approved: {decision.get('approved', False)}")
    print(f"   Position Size: {decision.get('position_size', 0)} shares")
    print(f"   Dollar Amount: ${decision.get('dollar_amount', 0):,.2f}")
    print(f"   Risk Level: {decision.get('risk_level', 'N/A')}")
    
    if decision.get("approved", False):
        print(f"\n⚡ Execution Agent executing approved trade...")
        execution_result = await coordinator.execution_agent.execute_approved_trade(risk_evaluation)
        
        print(f"\n⚡ Execution Result:")
        print(f"   Status: {execution_result.get('status', 'N/A')}")
        if execution_result.get('status') == 'SUCCESS':
            print(f"   Order ID: {execution_result.get('order_id', 'N/A')}")
            print(f"   Symbol: {execution_result.get('symbol', 'N/A')}")
            print(f"   Side: {execution_result.get('side', 'N/A')}")
            print(f"   Quantity: {execution_result.get('quantity', 0)} shares")
            print(f"   Expected Price: ${execution_result.get('expected_price', 0):.2f}")
            
            # Check order status
            order_id = execution_result.get('order_id')
            if order_id:
                print(f"\n📋 Checking order status...")
                await asyncio.sleep(1)  # Brief delay
                order_status = await coordinator.execution_agent.check_order_status(order_id)
                
                if "error" not in order_status:
                    print(f"   Order Status: {order_status.get('status', 'N/A')}")
                    print(f"   Filled Qty: {order_status.get('filled_qty', '0')}")
                    if order_status.get('filled_avg_price'):
                        print(f"   Fill Price: ${order_status.get('filled_avg_price', '0')}")
        else:
            print(f"   Error: {execution_result.get('reason', 'Unknown error')}")
    else:
        print(f"\n❌ Trade rejected: {decision.get('reasoning', 'Unknown reason')}")
    
    # Get execution summary
    print(f"\n📊 Execution Performance Summary:")
    execution_summary = await coordinator.execution_agent.get_execution_summary()
    
    if "error" not in execution_summary:
        metrics = execution_summary['execution_metrics']
        print(f"   Total Orders: {metrics['total_orders']}")
        print(f"   Fill Rate: {metrics['fill_rate_percent']:.1f}%")
        print(f"   Active Orders: {metrics['active_orders']}")
    else:
        print(f"   Error: {execution_summary['error']}")


if __name__ == "__main__":
    asyncio.run(test_execution_demo())