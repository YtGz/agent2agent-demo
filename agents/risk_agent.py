"""
Risk Assessment Agent - Evaluates portfolio risk and determines position sizing
"""
import json
import math
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import GetAssetsRequest
from alpaca.trading.enums import AssetClass
from .base_agent import BaseAgent


class RiskAgent(BaseAgent):
    """Agent responsible for risk assessment and position sizing"""
    
    def __init__(self, alpaca_api_key: str, alpaca_secret_key: str):
        super().__init__(
            name="risk_agent",
            instruction="""You are a sophisticated risk management agent. Your role is to:
            1. Evaluate trading signals from the Market Agent for risk appropriateness
            2. Calculate optimal position sizes based on portfolio risk metrics
            3. Enforce risk limits and concentration controls
            4. Assess portfolio-wide risk exposure and correlation
            5. Make approve/reject decisions on trade recommendations
            6. Communicate risk assessments to other agents via A2A protocol
            
            Always prioritize capital preservation and risk-adjusted returns.
            Provide clear reasoning for all risk decisions."""
        )
        
        self.alpaca_api_key = alpaca_api_key
        self.alpaca_secret_key = alpaca_secret_key
        self.trading_client = TradingClient(alpaca_api_key, alpaca_secret_key, paper=True)
        
        # Risk parameters
        self.max_portfolio_risk = 0.02  # 2% max portfolio risk per trade
        self.max_position_size = 0.1    # 10% max position size
        self.max_sector_exposure = 0.3  # 30% max sector exposure
        self.risk_free_rate = 0.045     # 4.5% risk-free rate
        self.initial_capital = 100000   # $100k starting capital
        
        # Portfolio state
        self.portfolio = {}
        self.cash = self.initial_capital
        self.positions = {}
        
    async def evaluate_trade_signal(self, market_signal: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate a trade signal from Market Agent and determine position sizing"""
        try:
            symbol = market_signal.get('symbol')
            signal = market_signal.get('ai_analysis', {}).get('signal', 'HOLD')
            confidence = market_signal.get('ai_analysis', {}).get('confidence', 0.5)
            price = market_signal.get('market_data', {}).get('price', 0)
            
            if not symbol or not price:
                return {"error": "Invalid market signal - missing symbol or price"}
            
            # Get current portfolio state
            await self._update_portfolio_state()
            
            # Calculate position sizing
            position_analysis = self._calculate_position_size(
                symbol, signal, confidence, price, market_signal
            )
            
            # Perform risk assessment
            risk_assessment = await self._assess_portfolio_risk(
                symbol, position_analysis, market_signal
            )
            
            # Make final decision
            decision = await self._make_risk_decision(
                symbol, signal, position_analysis, risk_assessment, market_signal
            )
            
            return {
                "symbol": symbol,
                "timestamp": datetime.now().isoformat(),
                "original_signal": signal,
                "confidence": confidence,
                "position_analysis": position_analysis,
                "risk_assessment": risk_assessment,
                "decision": decision,
                "reasoning": decision.get("reasoning", "")
            }
            
        except Exception as e:
            return {"error": str(e), "symbol": market_signal.get('symbol', 'UNKNOWN')}
    
    async def _update_portfolio_state(self):
        """Update current portfolio positions and cash"""
        try:
            # Get current positions
            positions = self.trading_client.get_all_positions()
            self.positions = {}
            
            for position in positions:
                self.positions[position.symbol] = {
                    "qty": float(position.qty),
                    "market_value": float(position.market_value),
                    "cost_basis": float(position.cost_basis),
                    "unrealized_pl": float(position.unrealized_pl),
                    "side": position.side
                }
            
            # Get account info
            account = self.trading_client.get_account()
            self.cash = float(account.cash)
            self.portfolio_value = float(account.portfolio_value)
            
        except Exception as e:
            # If API fails, use mock data for demo
            self.positions = {}
            self.cash = self.initial_capital
            self.portfolio_value = self.initial_capital
    
    def _calculate_position_size(self, symbol: str, signal: str, confidence: float, 
                               price: float, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate optimal position size using multiple methods"""
        
        if signal == "HOLD":
            return {
                "method": "HOLD",
                "shares": 0,
                "dollar_amount": 0,
                "portfolio_percentage": 0,
                "reasoning": "HOLD signal - no position change recommended"
            }
        
        # Method 1: Kelly Criterion (simplified)
        win_rate = min(confidence, 0.9)  # Cap at 90%
        avg_win = 0.15  # Assume 15% average win
        avg_loss = 0.08  # Assume 8% average loss
        kelly_fraction = (win_rate * avg_win - (1 - win_rate) * avg_loss) / avg_win
        kelly_fraction = max(0, min(kelly_fraction, 0.25))  # Cap at 25%
        
        # Method 2: Volatility-based sizing
        volatility = self._estimate_volatility(market_data)
        vol_adjusted_size = self.max_portfolio_risk / max(volatility, 0.01)
        
        # Method 3: Confidence-based sizing
        confidence_size = confidence * self.max_position_size
        
        # Take the minimum of all methods for conservative approach
        optimal_fraction = min(kelly_fraction, vol_adjusted_size, confidence_size)
        
        # Calculate dollar amount and shares
        dollar_amount = self.portfolio_value * optimal_fraction
        shares = int(dollar_amount / price)
        actual_dollar_amount = shares * price
        actual_percentage = actual_dollar_amount / self.portfolio_value
        
        return {
            "method": "KELLY_VOLATILITY_CONFIDENCE",
            "kelly_fraction": kelly_fraction,
            "volatility_fraction": vol_adjusted_size,
            "confidence_fraction": confidence_size,
            "optimal_fraction": optimal_fraction,
            "shares": shares,
            "dollar_amount": actual_dollar_amount,
            "portfolio_percentage": actual_percentage,
            "price": price,
            "estimated_volatility": volatility,
            "reasoning": f"Position size based on Kelly ({kelly_fraction:.1%}), volatility ({vol_adjusted_size:.1%}), and confidence ({confidence_size:.1%})"
        }
    
    def _estimate_volatility(self, market_data: Dict[str, Any]) -> float:
        """Estimate volatility from market data"""
        try:
            # Use price change percentage as volatility proxy
            price_change_pct = abs(market_data.get('market_data', {}).get('price_change_pct', 2.0))
            return price_change_pct / 100.0  # Convert to decimal
        except:
            return 0.02  # Default 2% volatility
    
    async def _assess_portfolio_risk(self, symbol: str, position_analysis: Dict[str, Any], 
                                   market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Assess portfolio-wide risk implications"""
        
        current_position_value = self.positions.get(symbol, {}).get("market_value", 0)
        new_position_value = position_analysis.get("dollar_amount", 0)
        total_position_value = abs(current_position_value) + abs(new_position_value)
        
        # Position concentration check
        position_concentration = total_position_value / self.portfolio_value
        concentration_risk = position_concentration > self.max_position_size
        
        # Portfolio risk check
        portfolio_risk = position_analysis.get("portfolio_percentage", 0)
        portfolio_risk_breach = portfolio_risk > self.max_portfolio_risk
        
        # Cash availability check
        cash_needed = new_position_value
        sufficient_cash = cash_needed <= self.cash
        
        # Calculate portfolio metrics
        total_positions_value = sum(abs(pos.get("market_value", 0)) for pos in self.positions.values())
        portfolio_utilization = total_positions_value / self.portfolio_value
        
        # Risk score calculation
        risk_factors = []
        if concentration_risk:
            risk_factors.append("position_concentration")
        if portfolio_risk_breach:
            risk_factors.append("portfolio_risk_limit")
        if not sufficient_cash:
            risk_factors.append("insufficient_cash")
        if portfolio_utilization > 0.8:
            risk_factors.append("high_portfolio_utilization")
        
        risk_score = len(risk_factors) / 4.0  # Normalize to 0-1
        
        # AI risk assessment
        risk_context = f"""
        Assess the portfolio risk for this trade:
        
        Symbol: {symbol}
        Position Size: ${new_position_value:,.2f} ({position_analysis.get('portfolio_percentage', 0):.1%} of portfolio)
        Current Cash: ${self.cash:,.2f}
        Portfolio Value: ${self.portfolio_value:,.2f}
        Position Concentration: {position_concentration:.1%}
        Portfolio Utilization: {portfolio_utilization:.1%}
        Risk Factors: {risk_factors}
        
        Provide a risk assessment with recommendation to APPROVE or REJECT this trade.
        Consider position sizing, concentration risk, and overall portfolio health.
        """
        
        ai_assessment = await self.process_message(risk_context)
        
        return {
            "position_concentration": position_concentration,
            "concentration_risk": concentration_risk,
            "portfolio_risk_breach": portfolio_risk_breach,
            "sufficient_cash": sufficient_cash,
            "cash_needed": cash_needed,
            "available_cash": self.cash,
            "portfolio_utilization": portfolio_utilization,
            "risk_factors": risk_factors,
            "risk_score": risk_score,
            "ai_assessment": ai_assessment,
            "risk_level": "HIGH" if risk_score > 0.6 else "MEDIUM" if risk_score > 0.3 else "LOW"
        }
    
    async def _make_risk_decision(self, symbol: str, signal: str, position_analysis: Dict[str, Any],
                                risk_assessment: Dict[str, Any], market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Make final approve/reject decision based on risk analysis"""
        
        # Automatic rejection criteria
        auto_reject = False
        rejection_reasons = []
        
        if not risk_assessment.get("sufficient_cash", True):
            auto_reject = True
            rejection_reasons.append("Insufficient cash")
        
        if risk_assessment.get("concentration_risk", False):
            auto_reject = True
            rejection_reasons.append("Position concentration limit exceeded")
        
        if risk_assessment.get("risk_score", 0) > 0.8:
            auto_reject = True
            rejection_reasons.append("Risk score too high")
        
        if signal == "HOLD":
            return {
                "action": "HOLD",
                "approved": False,
                "reasoning": "Market signal is HOLD - no action required"
            }
        
        if auto_reject:
            return {
                "action": "REJECT",
                "approved": False,
                "reasoning": f"Trade rejected: {', '.join(rejection_reasons)}",
                "rejection_reasons": rejection_reasons
            }
        
        # AI decision for edge cases
        decision_context = f"""
        Make a final trading decision based on this analysis:
        
        Symbol: {symbol}
        Market Signal: {signal}
        Position Size: {position_analysis.get('shares', 0)} shares (${position_analysis.get('dollar_amount', 0):,.2f})
        Portfolio Impact: {position_analysis.get('portfolio_percentage', 0):.1%}
        Risk Level: {risk_assessment.get('risk_level', 'UNKNOWN')}
        Risk Score: {risk_assessment.get('risk_score', 0):.2f}
        
        Decision options: APPROVE or REJECT
        
        Provide your decision with clear reasoning focused on risk management.
        Format your response as: DECISION: [APPROVE/REJECT] - [reasoning]
        """
        
        ai_decision = await self.process_message(decision_context)
        
        # Parse AI decision
        approved = "APPROVE" in ai_decision.upper()
        action = "APPROVE" if approved else "REJECT"
        
        return {
            "action": action,
            "approved": approved,
            "reasoning": ai_decision,
            "position_size": position_analysis.get("shares", 0),
            "dollar_amount": position_analysis.get("dollar_amount", 0),
            "portfolio_percentage": position_analysis.get("portfolio_percentage", 0),
            "risk_level": risk_assessment.get("risk_level", "MEDIUM")
        }
    
    async def get_portfolio_summary(self) -> Dict[str, Any]:
        """Get current portfolio summary for reporting"""
        await self._update_portfolio_state()
        
        total_unrealized_pl = sum(pos.get("unrealized_pl", 0) for pos in self.positions.values())
        total_market_value = sum(abs(pos.get("market_value", 0)) for pos in self.positions.values())
        
        return {
            "timestamp": datetime.now().isoformat(),
            "cash": self.cash,
            "portfolio_value": self.portfolio_value,
            "positions_count": len(self.positions),
            "total_market_value": total_market_value,
            "total_unrealized_pl": total_unrealized_pl,
            "portfolio_utilization": total_market_value / self.portfolio_value if self.portfolio_value > 0 else 0,
            "positions": self.positions,
            "risk_parameters": {
                "max_portfolio_risk": self.max_portfolio_risk,
                "max_position_size": self.max_position_size,
                "max_sector_exposure": self.max_sector_exposure
            }
        }
    
    def _get_specific_capabilities(self) -> Dict[str, Any]:
        """Define Risk Agent specific capabilities"""
        return {
            "functions": [
                "evaluate_trade_signal",
                "calculate_position_size",
                "assess_portfolio_risk",
                "make_risk_decision",
                "get_portfolio_summary"
            ],
            "risk_models": [
                "kelly_criterion",
                "volatility_based_sizing",
                "confidence_weighted_sizing",
                "portfolio_concentration_limits"
            ],
            "risk_metrics": [
                "position_concentration",
                "portfolio_utilization",
                "risk_score",
                "cash_management"
            ]
        }