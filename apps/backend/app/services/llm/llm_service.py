import logging
import time
import re
from typing import List
from pydantic import BaseModel
from fastapi import HTTPException
import google.generativeai as genai
from google.api_core import exceptions as google_exceptions

from app.core.config import settings

logger = logging.getLogger(__name__)

class LLMService:
    """
    Implementation of the LLM generation interface using Google Gemini.
    """
    
    def __init__(
        self,
        temperature: float = 0.0,
        top_p: float = 0.95,
        max_output_tokens: int = 1024,
    ):
        self.temperature = temperature
        self.top_p = top_p
        self.max_output_tokens = max_output_tokens
        
        self.api_key = settings.GEMINI_API_KEY
        self.model_name = settings.GEMINI_MODEL
        
        if not self.api_key:
            logger.warning("GEMINI_API_KEY is not set in the configuration.")

    def _build_prompt(self, actual_question: str, context: List[str]) -> str:
        """
        Constructs the strict RAG prompt according to requirements.
        """
        system_instruction = (
            "You are an Enterprise AI Assistant.\n\n"
            "Rules:\n"
            "- Answer ONLY using the supplied context.\n"
            "- Never use outside knowledge.\n"
            "- Never hallucinate.\n"
            "- If the answer is missing, reply exactly:\n"
            "\"I couldn't find this information in the uploaded documents.\"\n"
            "- Keep answers concise.\n"
            "- Use markdown formatting when appropriate.\n"
        )
        
        context_str = "\n".join(context)
        
        prompt_structure = (
            "================\n\n"
            "Context\n\n"
            f"{context_str}\n\n"
            "Question\n\n"
            f"{actual_question}\n\n"
            "Answer\n\n"
            "================"
        )
        
        return system_instruction + "\n" + prompt_structure

    def generate_answer(
        self,
        question: str,
        context: List[str]
    ) -> str:
        """
        Generates an answer based strictly on the provided context using Gemini.
        """
        if not self.api_key:
            raise HTTPException(status_code=500, detail="Gemini API key is not configured.")

        # chat_service.py passes a pre-built prompt as the `question` argument.
        # We need to extract the actual user question to construct the strict RAG prompt required.
        match = re.search(r"Question:\s*(.*?)\s*\n\nContext:", question, re.DOTALL)
        actual_question = match.group(1) if match else question

        genai.configure(api_key=self.api_key)
        
        try:
            model = genai.GenerativeModel(self.model_name)
        except Exception as e:
            logger.error(f"Failed to initialize Gemini model: {e}")
            raise HTTPException(status_code=500, detail="LLM Initialization failed.")

        prompt = self._build_prompt(actual_question, context)
        
        # Logging details
        retrieved_chunk_count = len(context)
        prompt_size = len(prompt)
        
        logger.info(f"Generating answer. Retrieved chunk count: {retrieved_chunk_count}, Prompt size (chars): {prompt_size}")
        
        start_time = time.time()
        
        try:
            response = model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=self.temperature,
                    top_p=self.top_p,
                    max_output_tokens=self.max_output_tokens,
                )
            )
            
            generation_time = time.time() - start_time
            logger.info(f"Answer generated successfully. Generation time: {generation_time:.4f}s")
            
            if not response.text:
                raise ValueError("Received empty response text from Gemini.")
                
            return response.text.strip()
            
        except google_exceptions.PermissionDenied as e:
            logger.error(f"Gemini API permission denied (invalid key?): {e}")
            raise HTTPException(status_code=401, detail="LLM API permission denied. Please check your API key.")
        except google_exceptions.ResourceExhausted as e:
            logger.error(f"Gemini API quota exceeded: {e}")
            raise HTTPException(status_code=429, detail="LLM API quota exceeded.")
        except google_exceptions.ServiceUnavailable as e:
            logger.error(f"Gemini API service unavailable (network/timeout): {e}")
            raise HTTPException(status_code=503, detail="LLM API is currently unavailable.")
        except google_exceptions.DeadlineExceeded as e:
            logger.error(f"Gemini API timeout: {e}")
            raise HTTPException(status_code=504, detail="LLM API request timed out.")
        except Exception as e:
            logger.error(f"Unexpected error during Gemini generation: {e}")
            raise HTTPException(status_code=500, detail="An unexpected error occurred during LLM generation.")

    def generate_structured(self, prompt: str, schema: type[BaseModel]) -> str:
        """
        Generates structured JSON output conforming to a Pydantic schema using Gemini.
        """
        if not self.api_key:
            raise HTTPException(status_code=500, detail="Gemini API key is not configured.")

        genai.configure(api_key=self.api_key)
        
        try:
            model = genai.GenerativeModel(self.model_name)
            
            logger.info(f"Generating structured answer. Prompt size: {len(prompt)}")
            start_time = time.time()
            
            response = model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.1,  # Low temp for deterministic structured output
                    top_p=self.top_p,
                    max_output_tokens=self.max_output_tokens,
                    response_mime_type="application/json",
                    response_schema=schema
                )
            )
            
            generation_time = time.time() - start_time
            logger.info(f"Structured answer generated successfully. Time: {generation_time:.4f}s")
            
            if not response.text:
                raise ValueError("Received empty response text from Gemini.")
                
            return response.text.strip()
            
        except google_exceptions.PermissionDenied as e:
            logger.error(f"Gemini API permission denied (invalid key?): {e}")
            raise HTTPException(status_code=401, detail="LLM API permission denied.")
        except Exception as e:
            logger.error(f"Unexpected error during structured generation: {e}")
            raise HTTPException(status_code=500, detail="An unexpected error occurred during LLM structured generation.")
