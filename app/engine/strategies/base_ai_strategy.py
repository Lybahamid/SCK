"""
Base class for AI-powered context generation strategies.

All AI strategies inherit from this to ensure consistent
prompt engineering, error handling, and output formatting.
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from pydantic import BaseModel

from app.models.schemas import Message, ParsedSession
from app.engine.extractors.state_extractor import StateExtractor, ExtractedState
from app.engine.llm.gemini_client import GeminiClient


class AIStrategyConfig(BaseModel):
    """Configuration for AI strategy behavior."""
    model: str = "gemini-2.5-flash-lite"
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    include_original_transcript: bool = True


class BaseAIStrategy(ABC):
    """
    Abstract base for AI-powered strategies.
    
    Enforces a consistent pipeline:
    1. Extract state signals from conversation
    2. Build deterministic prompt template
    3. Send to Gemini with signals + optional transcript
    4. Format and return structured output
    """

    def __init__(self, config: AIStrategyConfig = None):
        self.config = config or AIStrategyConfig()
        self.gemini_client = GeminiClient()
        self.state_extractor = StateExtractor()

    def generate(
        self,
        session: ParsedSession,
        target_platform: str = "generic"
    ) -> str:
        """
        Main entry point: Generate context using AI.
        
        Args:
            session: Parsed conversation session
            target_platform: Target AI platform (chatgpt, claude, gemini, generic)
            
        Returns:
            Generated context string ready to paste into new session
        """
        # Step 1: Extract signals
        state = self.state_extractor.extract(session)
        
        # Step 2: Build prompt
        prompt = self._build_prompt(session, state, target_platform)
        
        # Step 3: Call Gemini
        response = self.gemini_client.generate(
            prompt=prompt,
            model=self.config.model,
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens
        )
        
        # Step 4: Format output
        formatted = self._format_output(response, state, target_platform)
        
        return formatted

    @abstractmethod
    def _build_prompt(
        self,
        session: ParsedSession,
        state: ExtractedState,
        target_platform: str
    ) -> str:
        """
        Build the prompt to send to Gemini.
        
        Subclasses implement strategy-specific prompts.
        
        Args:
            session: Full conversation
            state: Extracted signals/state
            target_platform: Target platform for context
            
        Returns:
            Prompt string for Gemini
        """
        pass

    @abstractmethod
    def _format_output(
        self,
        response: str,
        state: ExtractedState,
        target_platform: str
    ) -> str:
        """
        Format Gemini's response into final context.
        
        Subclasses implement strategy-specific formatting.
        
        Args:
            response: Raw response from Gemini
            state: Extracted state for reference
            target_platform: Target platform
            
        Returns:
            Formatted context string
        """
        pass

    def _format_messages_for_prompt(self, messages: List[Message]) -> str:
        """
        Helper: Format messages for inclusion in prompt.
        
        Returns a nicely formatted conversation transcript.
        """
        formatted = []
        for msg in messages:
            role = msg.role.upper()
            formatted.append(f"{role}: {msg.content}")
        return "\n\n".join(formatted)

    def _build_system_context(self, state: ExtractedState) -> str:
        """
        Helper: Build a summary of extracted state for prompt context.
        
        This gives Gemini structured signals about the conversation.
        """
        parts = []
        
        if state.topic:
            parts.append(f"Topic: {state.topic}")
        
        if state.goal:
            parts.append(f"Goal: {state.goal}")
        
        if state.key_points:
            points_str = "\n  - ".join(state.key_points[:5])
            parts.append(f"Key Points:\n  - {points_str}")
        
        if state.current_progress:
            parts.append(f"Current Progress: {state.current_progress}")
        
        if state.blockers:
            blockers_str = "\n  - ".join(state.blockers[:3])
            parts.append(f"Blockers:\n  - {blockers_str}")
        
        if state.open_questions:
            questions_str = "\n  - ".join(state.open_questions[:3])
            parts.append(f"Open Questions:\n  - {questions_str}")
        
        if state.next_steps:
            steps_str = "\n  - ".join(state.next_steps[:3])
            parts.append(f"Next Steps:\n  - {steps_str}")
        
        return "\n\n".join(parts)