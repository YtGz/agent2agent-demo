"""
Main entry point for the Multi-Agent Trading Demo with A2A Protocol
"""
import os
import asyncio
from dotenv import load_dotenv
from agents.agent_coordinator import AgentCoordinator

load_dotenv()


async def demo_a2a_protocol():
    """Demonstrate A2A protocol communication between agents"""
    print("🚀 Multi-Agent Trading Demo with A2A Protocol")
    print("=" * 60)
    
    try:
        alpaca_api_key = os.getenv("ALPACA_API_KEY")
        alpaca_secret_key = os.getenv("ALPACA_SECRET_KEY")
        
        if not alpaca_api_key or not alpaca_secret_key:
            print("❌ Please set ALPACA_API_KEY and ALPACA_SECRET_KEY in .env file")
            return
        
        # Initialize Agent Coordinator
        print("🎯 Initializing Multi-Agent System...")
        coordinator = AgentCoordinator(alpaca_api_key, alpaca_secret_key)
        
        # Display agent capabilities
        print("\n🤖 Agent Capabilities (A2A Discovery):")
        capabilities = coordinator.get_agent_capabilities()
        for agent_name, caps in capabilities["registered_agents"].items():
            print(f"  📊 {agent_name}: {caps['name']}")
            print(f"     Functions: {', '.join(caps['capabilities'].get('functions', []))}")
        
        # Demo 1: Full trading workflow with execution
        print(f"\n" + "="*60)
        print("DEMO 1: Full Trading Workflow with A2A Protocol & Execution")
        print("="*60)
        
        result = await coordinator.full_trading_workflow("AAPL")
        
        if "error" not in result:
            market_data = result["market_analysis"]["market_data"]
            ai_analysis = result["market_analysis"]["ai_analysis"]
            decision = result["risk_evaluation"]["decision"]
            
            print(f"\n📊 Market Analysis Results:")
            print(f"   Price: ${market_data['price']:.2f}")
            print(f"   Signal: {ai_analysis.get('signal', 'N/A')}")
            print(f"   Confidence: {ai_analysis.get('confidence', 0):.2f}")
            
            print(f"\n🛡️  Risk Assessment Results:")
            print(f"   Decision: {decision.get('action', 'N/A')}")
            print(f"   Position Size: {decision.get('position_size', 0)} shares")
            print(f"   Risk Level: {decision.get('risk_level', 'N/A')}")
            
            execution_result = result.get("execution_result", {})
            print(f"\n⚡ Execution Results:")
            print(f"   Status: {execution_result.get('status', 'N/A')}")
            if execution_result.get('status') == 'SUCCESS':
                print(f"   Order ID: {execution_result.get('order_id', 'N/A')}")
                print(f"   Executed: {execution_result.get('quantity', 0)} shares")
        
        # Demo 2: Full watchlist scan with A2A protocol
        print(f"\n" + "="*60)
        print("DEMO 2: Full Watchlist Scan with A2A Protocol")
        print("="*60)
        
        watchlist_results = await coordinator.scan_watchlist_with_risk_assessment()
        
        # Demo 3: A2A Communication Log Analysis
        print(f"\n" + "="*60)
        print("DEMO 3: A2A Protocol Communication Analysis")
        print("="*60)
        
        comm_log = coordinator.get_communication_log()
        print(f"📡 Total A2A Messages: {len(comm_log)}")
        
        if comm_log:
            print("\n🔄 Recent A2A Communications:")
            for i, msg in enumerate(comm_log[-5:], 1):  # Show last 5 messages
                print(f"   {i}. {msg['from_agent']} → {msg['to_agent']}")
                print(f"      Type: {msg['message_type']}")
                print(f"      Content: {msg['content']}")
                if msg.get('response'):
                    print(f"      Response: {msg['response'].get('action', 'N/A')}")
                print()
        
        # Demo 4: Portfolio Status
        print(f"\n" + "="*60)
        print("DEMO 4: Portfolio Risk Management Status")
        print("="*60)
        
        portfolio_status = await coordinator.get_portfolio_status()
        print(f"💰 Portfolio Value: ${portfolio_status['portfolio_value']:,.2f}")
        print(f"💵 Available Cash: ${portfolio_status['cash']:,.2f}")
        print(f"📊 Portfolio Utilization: {portfolio_status['portfolio_utilization']:.1%}")
        print(f"📈 Positions: {portfolio_status['positions_count']}")
        
        print(f"\n🛡️  Risk Parameters:")
        risk_params = portfolio_status['risk_parameters']
        print(f"   Max Portfolio Risk: {risk_params['max_portfolio_risk']:.1%}")
        print(f"   Max Position Size: {risk_params['max_position_size']:.1%}")
        print(f"   Max Sector Exposure: {risk_params['max_sector_exposure']:.1%}")
        
        # Demo 5: Execution Performance
        print(f"\n" + "="*60)
        print("DEMO 5: Execution Performance Summary")
        print("="*60)
        
        execution_status = await coordinator.get_execution_status()
        if "error" not in execution_status:
            metrics = execution_status['execution_metrics']
            print(f"⚡ Execution Metrics:")
            print(f"   Total Orders: {metrics['total_orders']}")
            print(f"   Filled Orders: {metrics['filled_orders']}")
            print(f"   Fill Rate: {metrics['fill_rate_percent']:.1f}%")
            print(f"   Active Orders: {metrics['active_orders']}")
            
            if execution_status.get('recent_orders'):
                print(f"\n📋 Recent Orders:")
                for order in execution_status['recent_orders'][:3]:
                    if "error" not in order:
                        print(f"   {order.get('symbol', 'N/A')}: {order.get('status', 'N/A')} - {order.get('side', 'N/A')} {order.get('quantity', 0)} shares")
        else:
            print(f"⚠️  Execution status error: {execution_status['error']}")
        
        print(f"\n" + "="*60)
        print("🎉 A2A Protocol Demo Complete!")
        print(f"   Total Agent Communications: {len(comm_log)}")
        print(f"   Agents Coordinated: {len(capabilities['registered_agents'])}")
        print(f"   Symbols Analyzed: {len([r for r in watchlist_results if 'error' not in r])}")
        print("="*60)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """Main entry point"""
    await demo_a2a_protocol()


if __name__ == "__main__":
    asyncio.run(main())