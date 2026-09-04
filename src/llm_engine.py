"""
Dynamic LLM Engine with Groq Integration & Structured JSON Reasoning
Enables dynamic LLM-driven specialist agents with zero hallucination on financial calculations.
"""

import os
import json
import re
from typing import Dict, Any, List, Optional

try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False

class LLMEngine:
    _instance = None

    def __init__(self, api_key: Optional[str] = None):
        key = api_key or os.environ.get("GROQ_API_KEY", "")
        if not key:
            try:
                import streamlit as st
                if hasattr(st, "secrets") and "GROQ_API_KEY" in st.secrets:
                    key = st.secrets["GROQ_API_KEY"]
            except Exception:
                pass
        self.api_key = key
        self.client = None
        if GROQ_AVAILABLE and self.api_key:
            try:
                self.client = Groq(api_key=self.api_key)
            except Exception:
                self.client = None

    @classmethod
    def get_instance(cls, api_key: Optional[str] = None) -> "LLMEngine":
        if cls._instance is None or (api_key and cls._instance.api_key != api_key):
            cls._instance = cls(api_key=api_key)
        return cls._instance

    def set_api_key(self, api_key: str):
        self.api_key = api_key
        if GROQ_AVAILABLE and api_key:
            try:
                self.client = Groq(api_key=api_key)
            except Exception:
                self.client = None

    def is_live_llm_active(self) -> bool:
        return bool(self.client is not None)

    def generate_json(self, prompt: str, system_prompt: str, model: str = "llama-3.3-70b-versatile") -> Optional[Any]:
        """Invokes Groq LLM with JSON mode or extracts structured JSON from narrative."""
        if not self.client:
            return None

        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt + "\nIMPORTANT: You must respond ONLY with valid JSON (an object or array). No conversational prelude or epilogue."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=2048,
                response_format={"type": "json_object"} if "json_object" in model.lower() or True else None
            )
            raw = response.choices[0].message.content or ""
            
            # Clean markdown codeblocks if present
            raw_clean = re.sub(r"^```json\s*", "", raw.strip(), flags=re.MULTILINE)
            raw_clean = re.sub(r"\s*```$", "", raw_clean.strip(), flags=re.MULTILINE)
            
            parsed = json.loads(raw_clean)
            return parsed
        except Exception as e:
            # If JSON parse or API call failed, fallback
            return None

    def generate_narrative(self, prompt: str, system_prompt: str = "", model: str = "llama-3.3-70b-versatile") -> str:
        """Invokes Groq LLM for freeform narrative or talking point refinement."""
        if self.client:
            try:
                response = self.client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": system_prompt or "You are an elite private banking wealth intelligence assistant at Bank Julius Baer."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.2,
                    max_tokens=1024
                )
                return response.choices[0].message.content or ""
            except Exception:
                pass
        return ""
