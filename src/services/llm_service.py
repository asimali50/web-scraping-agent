"""LLM Service - Unified interface for multiple LLM providers (Groq, Gemini, Claude)"""

import os
from typing import Optional
from src.core.config import get_config
from src.services.logger_service import get_logger

logger = get_logger(__name__)


class LLMService:
    """Unified LLM service supporting multiple providers"""

    def __init__(self):
        """Initialize LLM service with configured provider"""
        self.config = get_config()
        self.provider = self.config.get("llm.provider", "groq").lower()
        self.model = self.config.get("llm.model", "mixtral-8x7b-32768")
        self.max_tokens = self.config.get("llm.max_tokens", 500)

        logger.info(f"LLM Service initialized with provider: {self.provider}, model: {self.model}")

        # Initialize provider-specific client
        self._init_provider()

    def _init_provider(self):
        """Initialize the configured LLM provider"""
        if self.provider == "groq":
            self._init_groq()
        elif self.provider == "gemini":
            self._init_gemini()
        elif self.provider == "claude":
            self._init_claude()
        else:
            logger.warning(f"Unknown provider: {self.provider}, falling back to Groq")
            self.provider = "groq"
            self._init_groq()

    def _init_groq(self):
        """Initialize Groq client"""
        try:
            from groq import Groq
            api_key = os.getenv("GROQ_API_KEY")
            if not api_key:
                raise ValueError("GROQ_API_KEY environment variable not set")
            self.client = Groq(api_key=api_key)
            logger.info("Groq client initialized successfully")
        except ImportError:
            logger.error("Groq package not installed. Install with: pip install groq")
            raise
        except Exception as e:
            logger.error(f"Failed to initialize Groq client: {e}")
            raise

    def _init_gemini(self):
        """Initialize Google Gemini client"""
        try:
            import google.generativeai as genai
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                raise ValueError("GEMINI_API_KEY environment variable not set")
            genai.configure(api_key=api_key)
            self.client = genai.GenerativeModel(self.model)
            logger.info("Google Gemini client initialized successfully")
        except ImportError:
            logger.error("google-generativeai package not installed. Install with: pip install google-generativeai")
            raise
        except Exception as e:
            logger.error(f"Failed to initialize Gemini client: {e}")
            raise

    def _init_claude(self):
        """Initialize Anthropic Claude client"""
        try:
            from anthropic import Anthropic
            api_key = os.getenv("CLAUDE_API_KEY")
            if not api_key:
                raise ValueError("CLAUDE_API_KEY environment variable not set")
            self.client = Anthropic(api_key=api_key)
            logger.info("Claude client initialized successfully")
        except ImportError:
            logger.error("anthropic package not installed. Install with: pip install anthropic")
            raise
        except Exception as e:
            logger.error(f"Failed to initialize Claude client: {e}")
            raise

    def query(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """
        Query the LLM with the given prompt

        Args:
            prompt: The user prompt
            system_prompt: Optional system message/context

        Returns:
            LLM response text
        """
        try:
            if self.provider == "groq":
                return self._query_groq(prompt, system_prompt)
            elif self.provider == "gemini":
                return self._query_gemini(prompt, system_prompt)
            elif self.provider == "claude":
                return self._query_claude(prompt, system_prompt)
        except Exception as e:
            logger.error(f"LLM query failed with {self.provider}: {e}")
            raise

    def _query_groq(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Query Groq API"""
        messages = []

        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        messages.append({"role": "user", "content": prompt})

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=self.max_tokens,
            temperature=0.3,  # Low temperature for deterministic matching
        )

        return response.choices[0].message.content

    def _query_gemini(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Query Google Gemini API"""
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"

        response = self.client.generate_content(
            full_prompt,
            generation_config={
                "max_output_tokens": self.max_tokens,
                "temperature": 0.3,
            }
        )

        return response.text

    def _query_claude(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Query Claude API"""
        response = self.client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            system=system_prompt or "You are a helpful assistant for brand matching.",
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        return response.content[0].text

    def verify_match(
        self,
        brand_name: str,
        website_url: str,
        website_content: str,
        confidence: float
    ) -> dict:
        """
        Use LLM to verify brand-website match (when confidence is ambiguous)

        Args:
            brand_name: Brand name from Amazon
            website_url: Potential brand website URL
            website_content: Sample content from the website
            confidence: Current confidence score (0-100)

        Returns:
            Dict with verified flag and reasoning
        """
        system_prompt = """You are an expert at verifying if a website belongs to a brand.
Analyze the brand name, website URL, and content to determine if they match.
Respond ONLY in JSON format: {"verified": true/false, "reason": "short explanation"}"""

        prompt = f"""Brand: {brand_name}
Website URL: {website_url}
Website Content: {website_content[:500]}
Current Confidence: {confidence}%

Does this website belong to this brand? Respond in JSON format."""

        try:
            response = self.query(prompt, system_prompt)

            # Parse JSON response
            import json
            result = json.loads(response)
            logger.info(f"LLM verification for {brand_name}: {result}")
            return result

        except Exception as e:
            logger.warning(f"LLM verification failed, using confidence score: {e}")
            return {
                "verified": confidence >= 75,
                "reason": f"Fallback to confidence score ({confidence}%)"
            }


# Singleton instance
_llm_service = None


def get_llm_service() -> LLMService:
    """Get or create LLM service singleton"""
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service
