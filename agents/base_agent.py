"""
Base Agent class for the multi-agent trading system
"""
import os
import asyncio
from typing import Dict, Any, Optional
from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from dotenv import load_dotenv

load_dotenv()


class BaseAgent:
    """Base class for all trading agents"""
    
    def __init__(self, name: str, instruction: str, model: str = "anthropic/claude-3-sonnet-20240229"):
        self.name = name
        self.instruction = instruction
        self.model = model
        self._agent = None
        self._runner = None
        self._setup_agent()
    
    def _setup_agent(self):
        """Initialize the ADK agent with Claude model"""
        self._agent = LlmAgent(
            model=LiteLlm(model=self.model),
            name=self.name,
            instruction=self.instruction
        )
        
        # Create runner for agent execution
        session_service = InMemorySessionService()
        self._runner = Runner(
            agent=self._agent,
            app_name=self.name,
            session_service=session_service
        )
    
    async def process_message(self, message: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Process a message and return response"""
        if context:
            # Add context to the message
            context_str = "\n".join([f"{k}: {v}" for k, v in context.items()])
            full_message = f"Context:\n{context_str}\n\nMessage: {message}"
        else:
            full_message = message
        
        # Run the agent asynchronously
        return await self._run_agent_async(full_message)
    
    async def _run_agent_async(self, message: str) -> str:
        """Run the agent asynchronously and return response"""
        response_text = ""
        
        # Create session if it doesn't exist
        session_service = self._runner.session_service
        try:
            await session_service.get_session("session_1")
        except:
            await session_service.create_session(
                app_name=self.name,
                user_id="user_1",
                session_id="session_1"
            )
        
        # Create proper message format
        user_content = types.Content(
            role='user', 
            parts=[types.Part(text=message)]
        )
        
        async for event in self._runner.run_async(
            user_id="user_1",
            session_id="session_1", 
            new_message=user_content
        ):
            # Look for the final response event
            if hasattr(event, 'content') and event.content:
                response_text = event.content
            elif hasattr(event, 'message') and event.message:
                response_text = event.message
            elif hasattr(event, 'text') and event.text:
                response_text = event.text
        
        return response_text if response_text else "No response generated"
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Return agent capabilities for A2A protocol"""
        return {
            "name": self.name,
            "description": self.instruction,
            "model": self.model,
            "capabilities": self._get_specific_capabilities()
        }
    
    def _get_specific_capabilities(self) -> Dict[str, Any]:
        """Override in subclasses to define specific capabilities"""
        return {}