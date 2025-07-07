"""
Execution Agent - Handles order placement and trade execution via Alpaca Markets
"""
import json
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest, LimitOrderRequest, StopLossRequest
from alpaca.trading.enums import OrderSide, OrderType, TimeInForce, OrderClass
from alpaca.trading.models import Order
from .base_agent import BaseAgent


class ExecutionAgent(BaseAgent):
    """Agent responsible for order execution and trade management"""
    
    def __init__(self, alpaca_api_key: str, alpaca_secret_key: str):
        super().__init__(
            name="execution_agent",
            instruction="""You are a sophisticated trade execution agent. Your role is to:
            1. Receive approved trades from the Risk Agent via A2A protocol
            2. Execute orders through Alpaca Markets paper trading API
            3. Manage order lifecycle (pending, filled, cancelled, rejected)
            4. Optimize execution timing and order routing
            5. Handle order modifications and cancellations
            6. Report execution status back to other agents via A2A protocol
            7. Maintain audit trail of all trading activities
            
            Always ensure best execution practices and proper order management.
            Provide clear status updates for all trading activities."""
        )
        
        self.alpaca_api_key = alpaca_api_key
        self.alpaca_secret_key = alpaca_secret_key
        self.trading_client = TradingClient(alpaca_api_key, alpaca_secret_key, paper=True)
        
        # Execution parameters
        self.max_order_retry = 3
        self.order_timeout_minutes = 30
        self.slippage_tolerance = 0.005  # 0.5% slippage tolerance
        
        # Order tracking
        self.active_orders = {}
        self.execution_history = []
    
    async def execute_approved_trade(self, risk_decision: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a trade that has been approved by the Risk Agent"""
        try:
            # Validate trade approval - check both top level and nested decision
            decision = risk_decision.get("decision", {})
            approved = risk_decision.get("approved", False) or decision.get("approved", False)
            
            if not approved:
                return {
                    "status": "REJECTED",
                    "reason": "Trade not approved by Risk Agent",
                    "decision": risk_decision
                }
            
            symbol = risk_decision.get("symbol", "")
            position_size = risk_decision.get("decision", {}).get("position_size", 0)
            signal = risk_decision.get("original_signal", "HOLD")
            
            if not symbol or position_size <= 0 or signal == "HOLD":
                return {
                    "status": "NO_ACTION",
                    "reason": f"No execution needed - signal: {signal}, size: {position_size}",
                    "symbol": symbol
                }
            
            # Determine order side
            order_side = OrderSide.BUY if signal == "BUY" else OrderSide.SELL
            
            # Get current market price for execution analysis
            current_price = await self._get_current_price(symbol)
            if not current_price:
                return {
                    "status": "ERROR",
                    "reason": f"Unable to get current price for {symbol}",
                    "symbol": symbol
                }
            
            # Create and submit order
            order_result = await self._place_market_order(
                symbol, position_size, order_side, current_price, risk_decision
            )
            
            if order_result.get("status") == "SUCCESS":
                # Log execution
                execution_record = {
                    "execution_id": str(uuid.uuid4()),
                    "timestamp": datetime.now().isoformat(),
                    "symbol": symbol,
                    "side": order_side.value,
                    "quantity": position_size,
                    "order_id": order_result.get("order_id"),
                    "expected_price": current_price,
                    "risk_decision": risk_decision,
                    "status": "SUBMITTED"
                }
                self.execution_history.append(execution_record)
                
                # AI analysis of execution
                execution_analysis = await self._analyze_execution(
                    symbol, order_side, position_size, current_price, order_result
                )
                
                return {
                    "status": "SUCCESS",
                    "execution_id": execution_record["execution_id"],
                    "order_id": order_result.get("order_id"),
                    "symbol": symbol,
                    "side": order_side.value,
                    "quantity": position_size,
                    "expected_price": current_price,
                    "order_details": order_result,
                    "execution_analysis": execution_analysis,
                    "timestamp": execution_record["timestamp"]
                }
            else:
                return {
                    "status": "FAILED",
                    "reason": order_result.get("error", "Unknown execution error"),
                    "symbol": symbol,
                    "side": order_side.value,
                    "quantity": position_size
                }
                
        except Exception as e:
            return {
                "status": "ERROR",
                "error": str(e),
                "symbol": risk_decision.get("symbol", "UNKNOWN")
            }
    
    async def _get_current_price(self, symbol: str) -> Optional[float]:
        """Get current market price for a symbol"""
        try:
            # In a real implementation, we'd get real-time quotes
            # For paper trading demo, we'll use a mock price based on recent data
            # This simulates getting the current bid/ask spread
            
            # Mock current price (in real implementation, use market data API)
            mock_prices = {
                "AAPL": 213.55,
                "GOOGL": 179.53, 
                "MSFT": 498.84,
                "TSLA": 315.35,
                "NVDA": 159.34
            }
            
            return mock_prices.get(symbol, 100.0)  # Default price for unknown symbols
            
        except Exception:
            return None
    
    async def _place_market_order(self, symbol: str, quantity: int, side: OrderSide, 
                                 current_price: float, context: Dict[str, Any]) -> Dict[str, Any]:
        """Place a market order through Alpaca API"""
        try:
            # Create market order request
            market_order_data = MarketOrderRequest(
                symbol=symbol,
                qty=quantity,
                side=side,
                time_in_force=TimeInForce.DAY
            )
            
            # Submit order to Alpaca
            order = self.trading_client.submit_order(order_data=market_order_data)
            
            # Track the order
            self.active_orders[order.id] = {
                "order": order,
                "submitted_at": datetime.now(),
                "symbol": symbol,
                "quantity": quantity,
                "side": side.value,
                "expected_price": current_price,
                "context": context
            }
            
            return {
                "status": "SUCCESS",
                "order_id": str(order.id),
                "symbol": symbol,
                "quantity": quantity,
                "side": side.value,
                "order_type": "MARKET",
                "time_in_force": "DAY",
                "submitted_at": datetime.now().isoformat(),
                "alpaca_order": {
                    "id": str(order.id),
                    "status": order.status.value,
                    "filled_qty": str(order.filled_qty) if order.filled_qty else "0",
                    "filled_avg_price": str(order.filled_avg_price) if order.filled_avg_price else None
                }
            }
            
        except Exception as e:
            return {
                "status": "ERROR",
                "error": str(e),
                "symbol": symbol,
                "quantity": quantity,
                "side": side.value
            }
    
    async def _analyze_execution(self, symbol: str, side: OrderSide, quantity: int,
                               expected_price: float, order_result: Dict[str, Any]) -> str:
        """AI analysis of trade execution quality"""
        
        analysis_context = f"""
        Analyze this trade execution:
        
        Symbol: {symbol}
        Side: {side.value}
        Quantity: {quantity} shares
        Expected Price: ${expected_price:.2f}
        Order Type: Market Order
        Order Status: {order_result.get('status', 'UNKNOWN')}
        Order ID: {order_result.get('order_id', 'N/A')}
        
        Execution Context:
        - Paper trading environment
        - Market order for immediate execution
        - Risk-approved position size
        
        Provide a brief analysis of the execution quality and any observations.
        Focus on execution efficiency and order management.
        """
        
        return await self.process_message(analysis_context)
    
    async def check_order_status(self, order_id: str) -> Dict[str, Any]:
        """Check the status of a specific order"""
        try:
            order = self.trading_client.get_order_by_id(order_id)
            
            # Update our tracking
            if order_id in self.active_orders:
                self.active_orders[order_id]["last_checked"] = datetime.now()
            
            return {
                "order_id": str(order.id),
                "symbol": order.symbol,
                "status": order.status.value,
                "side": order.side.value,
                "quantity": str(order.qty),
                "filled_qty": str(order.filled_qty) if order.filled_qty else "0",
                "filled_avg_price": str(order.filled_avg_price) if order.filled_avg_price else None,
                "submitted_at": order.submitted_at.isoformat() if order.submitted_at else None,
                "filled_at": order.filled_at.isoformat() if order.filled_at else None,
                "time_in_force": order.time_in_force.value if order.time_in_force else None
            }
            
        except Exception as e:
            return {
                "error": str(e),
                "order_id": order_id
            }
    
    async def get_all_orders(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent orders from Alpaca"""
        try:
            orders = self.trading_client.get_orders(
                status="all",
                limit=limit,
                nested=True
            )
            
            order_list = []
            for order in orders:
                order_dict = {
                    "order_id": str(order.id),
                    "symbol": order.symbol,
                    "status": order.status.value,
                    "side": order.side.value,
                    "quantity": str(order.qty),
                    "filled_qty": str(order.filled_qty) if order.filled_qty else "0",
                    "filled_avg_price": str(order.filled_avg_price) if order.filled_avg_price else None,
                    "submitted_at": order.submitted_at.isoformat() if order.submitted_at else None,
                    "filled_at": order.filled_at.isoformat() if order.filled_at else None,
                    "order_type": order.order_type.value if order.order_type else None
                }
                order_list.append(order_dict)
            
            return order_list
            
        except Exception as e:
            return [{"error": str(e)}]
    
    async def cancel_order(self, order_id: str, reason: str = "Manual cancellation") -> Dict[str, Any]:
        """Cancel an active order"""
        try:
            self.trading_client.cancel_order_by_id(order_id)
            
            # Remove from active tracking
            if order_id in self.active_orders:
                del self.active_orders[order_id]
            
            # AI analysis of cancellation
            cancel_analysis = await self.process_message(f"""
            Order {order_id} was cancelled. Reason: {reason}
            
            Provide a brief analysis of this order cancellation and its implications.
            """)
            
            return {
                "status": "CANCELLED",
                "order_id": order_id,
                "reason": reason,
                "cancelled_at": datetime.now().isoformat(),
                "analysis": cancel_analysis
            }
            
        except Exception as e:
            return {
                "status": "ERROR",
                "error": str(e),
                "order_id": order_id
            }
    
    async def get_execution_summary(self) -> Dict[str, Any]:
        """Get summary of execution performance"""
        try:
            # Get recent orders for analysis
            recent_orders = await self.get_all_orders(limit=20)
            
            # Calculate execution metrics
            total_orders = len([o for o in recent_orders if "error" not in o])
            filled_orders = len([o for o in recent_orders if o.get("status") == "filled"])
            pending_orders = len([o for o in recent_orders if o.get("status") in ["new", "pending_new", "accepted"]])
            cancelled_orders = len([o for o in recent_orders if o.get("status") == "cancelled"])
            
            fill_rate = (filled_orders / total_orders * 100) if total_orders > 0 else 0
            
            # AI analysis of execution performance
            performance_analysis = await self.process_message(f"""
            Analyze the execution performance:
            
            Total Orders: {total_orders}
            Filled Orders: {filled_orders}
            Pending Orders: {pending_orders}
            Cancelled Orders: {cancelled_orders}
            Fill Rate: {fill_rate:.1f}%
            
            Recent Execution History: {len(self.execution_history)} recorded executions
            Active Orders: {len(self.active_orders)}
            
            Provide an assessment of execution quality and any recommendations.
            """)
            
            return {
                "timestamp": datetime.now().isoformat(),
                "execution_metrics": {
                    "total_orders": total_orders,
                    "filled_orders": filled_orders,
                    "pending_orders": pending_orders,
                    "cancelled_orders": cancelled_orders,
                    "fill_rate_percent": fill_rate,
                    "active_orders": len(self.active_orders),
                    "execution_history_count": len(self.execution_history)
                },
                "recent_orders": recent_orders[:5],  # Last 5 orders
                "performance_analysis": performance_analysis,
                "execution_parameters": {
                    "max_order_retry": self.max_order_retry,
                    "order_timeout_minutes": self.order_timeout_minutes,
                    "slippage_tolerance": self.slippage_tolerance
                }
            }
            
        except Exception as e:
            return {
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def _get_specific_capabilities(self) -> Dict[str, Any]:
        """Define Execution Agent specific capabilities"""
        return {
            "functions": [
                "execute_approved_trade",
                "check_order_status", 
                "get_all_orders",
                "cancel_order",
                "get_execution_summary"
            ],
            "order_types": [
                "market_orders",
                "limit_orders", 
                "stop_loss_orders"
            ],
            "execution_features": [
                "real_time_execution",
                "order_lifecycle_management",
                "execution_quality_analysis",
                "slippage_monitoring"
            ],
            "integrations": [
                "alpaca_markets_api",
                "paper_trading",
                "order_management_system"
            ]
        }