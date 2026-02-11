from typing import List, Dict, Optional, Any
from agent.utils.config import config
from agent.utils.logger import logger
from openai import OpenAI
import json
import re

class LLMClient:
    def __init__(self):
        self.api_key = config.get("llm.api_key", "lm-studio")
        self.base_url = config.get("llm.api_base", "http://127.0.0.1:1234/v1")
        self.llm_model_name = config.get("llm.model", "gpt-3.5-turbo")
        
        logger.info(f"Initializing LLM Client with base_url: {self.base_url}")
        
        self.client = OpenAI(
            base_url=self.base_url,
            api_key=self.api_key
        )
        
        # Logic to bypass OpenAI library validation for local servers
        if "localhost" in self.base_url or "127.0.0.1" in self.base_url:
            self.model_name = "gpt-3.5-turbo" # Override to pass client validation
            logger.info(f"Local LLM detected. Using '{self.model_name}' as alias for '{self.llm_model_name}'")
        else:
            self.model_name = self.llm_model_name

    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """
        Generates a response from the LLM.
        """
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        try:
            logger.debug(f"LLM Request: {messages}")
            completion = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=0.7
            )
            response = completion.choices[0].message.content
            logger.debug(f"LLM Response: {response[:100]}...")
            return response
        except Exception as e:
            logger.error(f"LLM Generation failed: {e}")
            return f"Error generating response: {e}"

    def generate_structured(self, prompt: str, example_schema: Dict[str, Any], system_prompt: Optional[str] = None, max_retries: int = 3) -> Dict[str, Any]:
        """
        Generates a structured JSON response.
        """
        schema_str = json.dumps(example_schema, indent=2)
        system_instruction = f"""
You are a precise JSON generator. 
You must output VALID JSON matching exactly this schema:
{schema_str}
Do not output any markdown formatting like ```json or ```. Just the raw JSON object.
"""
        
        final_system_prompt = system_prompt + "\n" + system_instruction if system_prompt else system_instruction
        
        current_prompt = prompt
        
        for attempt in range(max_retries):
            response = self.generate(current_prompt, system_prompt=final_system_prompt)
            
            # Cleaning response
            cleaned_response = response.strip()
            # Remove markdown code blocks if present
            cleaned_response = re.sub(r'^```json\s*', '', cleaned_response)
            cleaned_response = re.sub(r'^```\s*', '', cleaned_response)
            cleaned_response = re.sub(r'\s*```$', '', cleaned_response)
            
            # Try finding JSON object
            match = re.search(r'\{[\s\S]*\}', cleaned_response)
            if match:
                cleaned_response = match.group(0)
            
            try:
                return json.loads(cleaned_response)
            except json.JSONDecodeError as e:
                logger.warning(f"JSON Parse Error (Attempt {attempt+1}): {e}")
                current_prompt = prompt + f"\n\nError: Previous output was not valid JSON. \nOutput: {response}\nError: {str(e)}\nPlease correct it."
                
        raise ValueError("Failed to generate valid JSON after retries.")

    def chat(self, messages: List[Dict[str, str]]) -> str:
        """
        Chat completion interface.
        """
        try:
            completion = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=0.7
            )
            return completion.choices[0].message.content
        except Exception as e:
            logger.error(f"LLM Chat failed: {e}")
            return f"Error in chat: {e}"
