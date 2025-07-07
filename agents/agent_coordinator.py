"""
Agent Coordinator - Manages A2A protocol communication between agents
"""
import asyncio
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from .market_agent import MarketAgent
from .risk_agent import RiskAgent
from .execution_agent import ExecutionAgent


class AgentCoordinator:
    """Coordinates communication between agents using A2A protocol"""
    
    def __init__(self, alpaca_api_key: str, alpaca_secret_key: str):
        # Initialize agents
        self.market_agent = MarketAgent(alpaca_api_key, alpaca_secret_key)
        self.risk_agent = RiskAgent(alpaca_api_key, alpaca_secret_key)
        self.execution_agent = ExecutionAgent(alpaca_api_key, alpaca_secret_key)
        
        # Communication logs for A2A protocol demonstration
        self.communication_log = []
        self.agent_registry = {
            "market_agent": self.market_agent,
            "risk_agent": self.risk_agent,
            "execution_agent": self.execution_agent
        }
    
    def log_communication(self, from_agent: str, to_agent: str, message_type: str, 
                         content: Dict[str, Any], response: Optional[Dict[str, Any]] = None):
        """Log inter-agent communication for A2A protocol tracking"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "from_agent": from_agent,
            "to_agent": to_agent,
            "message_type": message_type,
            "content": content,
            "response": response,
            "protocol": "A2A"
        }
        self.communication_log.append(log_entry)
        
        # Print for demo visualization
        print(f"\n🔄 A2A Communication:")
        print(f"   {from_agent} → {to_agent}")
        print(f"   Type: {message_type}")
        print(f"   Content: {content.get('symbol', 'N/A')} - {content.get('signal', content.get('action', 'N/A'))}")
        if response and "approved" in response:
            status = "✅ APPROVED" if response["approved"] else "❌ REJECTED"
            print(f"   Response: {status}")
    
    async def full_trading_workflow(self, symbol: str) -> Dict[str, Any]:
        """Complete workflow: Market analysis → Risk assessment → Execution"""
        
        print(f"\n🎯 Starting FULL TRADING WORKFLOW for {symbol}")
        print("=" * 60)
        
        # Step 1: Market Agent analyzes the symbol
        print(f"📊 Market Agent analyzing {symbol}...")
        market_analysis = await self.market_agent.analyze_stock(symbol)
        
        if "error" in market_analysis:
            return {"error": f"Market analysis failed: {market_analysis['error']}"}
        
        # Log A2A communication
        self.log_communication(
            from_agent="market_agent",
            to_agent="risk_agent", 
            message_type="TRADING_SIGNAL",
            content={
                "symbol": symbol,
                "signal": market_analysis.get("ai_analysis", {}).get("signal", "HOLD"),
                "confidence": market_analysis.get("ai_analysis", {}).get("confidence", 0.5),
                "price": market_analysis.get("market_data", {}).get("price", 0)
            }
        )
        
        # Step 2: Risk Agent evaluates the signal
        print(f"🛡️  Risk Agent evaluating signal...")
        risk_evaluation = await self.risk_agent.evaluate_trade_signal(market_analysis)
        
        if "error" in risk_evaluation:
            return {"error": f"Risk evaluation failed: {risk_evaluation['error']}"}
        
        # Log A2A response
        self.log_communication(
            from_agent="risk_agent",
            to_agent="execution_agent",
            message_type="RISK_DECISION", 
            content=risk_evaluation.get("decision", {}),
            response=risk_evaluation.get("decision", {})
        )
        
        # Step 3: Execution Agent executes if approved
        execution_result = {"status": "SKIPPED", "reason": "No execution needed"}
        
        if risk_evaluation.get("decision", {}).get("approved", False):
            print(f"⚡ Execution Agent executing trade...")
            execution_result = await self.execution_agent.execute_approved_trade(risk_evaluation)
            
            # Log A2A execution communication
            self.log_communication(
                from_agent="execution_agent",
                to_agent="reporting_agent",
                message_type="EXECUTION_RESULT",
                content={
                    "symbol": symbol,
                    "status": execution_result.get("status", "UNKNOWN"),
                    "order_id": execution_result.get("order_id", "N/A"),
                    "quantity": execution_result.get("quantity", 0)
                },
                response=execution_result
            )
        else:
            print(f"❌ Trade not approved - no execution")
        
        # Step 4: Compile complete workflow result
        workflow_result = {
            "symbol": symbol,
            "timestamp": datetime.now().isoformat(),
            "workflow_status": "COMPLETED",
            "market_analysis": market_analysis,
            "risk_evaluation": risk_evaluation,
            "execution_result": execution_result,
            "final_status": execution_result.get("status", "NOT_EXECUTED"),
            "a2a_communications": len(self.communication_log)
        }
        
        # Print summary
        decision = risk_evaluation.get("decision", {})
        if execution_result.get("status") == "SUCCESS":
            print(f"✅ TRADE EXECUTED: {execution_result.get('quantity', 0)} shares of {symbol}")
            print(f"   Order ID: {execution_result.get('order_id', 'N/A')}")
            print(f"   Expected Price: ${execution_result.get('expected_price', 0):.2f}")
        elif decision.get("approved", False):
            print(f"⚠️  EXECUTION FAILED: {execution_result.get('reason', 'Unknown error')}")
        else:
            print(f"❌ TRADE REJECTED: {decision.get('reasoning', 'Risk assessment rejected')}")
        
        return workflow_result

    async def analyze_and_assess_symbol(self, symbol: str) -> Dict[str, Any]:
        """Full workflow: Market analysis → Risk assessment → Decision"""
        
        print(f"\n🎯 Starting analysis workflow for {symbol}")
        print("=" * 50)
        
        # Step 1: Market Agent analyzes the symbol
        print(f"📊 Market Agent analyzing {symbol}...")
        market_analysis = await self.market_agent.analyze_stock(symbol)
        
        if "error" in market_analysis:
            return {"error": f"Market analysis failed: {market_analysis['error']}"}
        
        # Log A2A communication
        self.log_communication(
            from_agent="market_agent",
            to_agent="risk_agent", 
            message_type="TRADING_SIGNAL",
            content={
                "symbol": symbol,
                "signal": market_analysis.get("ai_analysis", {}).get("signal", "HOLD"),
                "confidence": market_analysis.get("ai_analysis", {}).get("confidence", 0.5),
                "price": market_analysis.get("market_data", {}).get("price", 0)
            }
        )
        
        # Step 2: Risk Agent evaluates the signal
        print(f"🛡️  Risk Agent evaluating signal...")
        risk_evaluation = await self.risk_agent.evaluate_trade_signal(market_analysis)
        
        if "error" in risk_evaluation:
            return {"error": f"Risk evaluation failed: {risk_evaluation['error']}"}
        
        # Log A2A response
        self.log_communication(
            from_agent="risk_agent",
            to_agent="market_agent",
            message_type="RISK_DECISION", 
            content=risk_evaluation.get("decision", {}),
            response=risk_evaluation.get("decision", {})
        )
        
        # Step 3: Compile complete workflow result
        workflow_result = {
            "symbol": symbol,
            "timestamp": datetime.now().isoformat(),
            "workflow_status": "COMPLETED",
            "market_analysis": market_analysis,
            "risk_evaluation": risk_evaluation,
            "final_decision": risk_evaluation.get("decision", {}),
            "a2a_communications": len(self.communication_log)
        }
        
        # Print summary
        decision = risk_evaluation.get("decision", {})
        if decision.get("approved", False):
            print(f"✅ APPROVED: {decision.get('position_size', 0)} shares of {symbol}")
            print(f"   Amount: ${decision.get('dollar_amount', 0):,.2f}")
            print(f"   Risk Level: {decision.get('risk_level', 'N/A')}")
        else:
            print(f"❌ REJECTED: {symbol}")
            print(f"   Reason: {decision.get('reasoning', 'N/A')}")
        
        return workflow_result
    
    async def scan_watchlist_with_risk_assessment(self) -> List[Dict[str, Any]]:
        """Scan entire watchlist with full Market → Risk agent workflow"""
        
        print(f"\n🔍 Scanning watchlist with risk assessment")
        print("=" * 60)
        
        results = []
        
        # Get watchlist from market agent
        watchlist = self.market_agent.watchlist
        
        for symbol in watchlist:
            try:
                result = await self.analyze_and_assess_symbol(symbol)
                results.append(result)
                
                # Small delay to make demo more visible
                await asyncio.sleep(0.5)
                
            except Exception as e:
                error_result = {
                    "symbol": symbol,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }
                results.append(error_result)
        
        # Print summary
        print(f"\n📋 Watchlist Summary:")
        print("-" * 40)
        approved_count = 0
        rejected_count = 0
        
        for result in results:
            if "error" not in result:
                decision = result.get("risk_evaluation", {}).get("decision", {})
                symbol = result.get("symbol", "N/A")
                
                if decision.get("approved", False):
                    approved_count += 1
                    shares = decision.get("position_size", 0)
                    amount = decision.get("dollar_amount", 0)
                    print(f"  ✅ {symbol}: {shares} shares (${amount:,.2f})")
                else:
                    rejected_count += 1
                    print(f"  ❌ {symbol}: REJECTED")
        
        print(f"\n📊 Results: {approved_count} approved, {rejected_count} rejected")
        print(f"🔄 A2A Communications: {len(self.communication_log)} messages")
        
        return results
    
    def get_agent_capabilities(self) -> Dict[str, Any]:
        """Get capabilities of all registered agents for A2A discovery"""
        capabilities = {}
        
        for agent_name, agent in self.agent_registry.items():
            capabilities[agent_name] = agent.get_capabilities()
        
        return {
            "coordinator_info": {
                "name": "agent_coordinator",
                "version": "1.0.0",
                "protocol": "A2A",
                "timestamp": datetime.now().isoformat()
            },
            "registered_agents": capabilities,
            "communication_log_size": len(self.communication_log)
        }
    
    def get_communication_log(self) -> List[Dict[str, Any]]:
        """Get A2A protocol communication history"""
        return self.communication_log
    
    async def get_portfolio_status(self) -> Dict[str, Any]:
        """Get comprehensive portfolio status from Risk Agent"""
        return await self.risk_agent.get_portfolio_summary()
    
    async def get_execution_status(self) -> Dict[str, Any]:
        """Get execution performance summary from Execution Agent"""
        return await self.execution_agent.get_execution_summary()