import yaml
import os
from typing import Dict

class PromptLoader:
    _instance = None
    _templates = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(PromptLoader, cls).__new__(cls)
            cls._instance._load_templates()
        return cls._instance

    def _load_templates(self):
        prompt_path = os.path.join(os.getcwd(), 'agent', 'prompts', 'templates.yaml')
        if os.path.exists(prompt_path):
            with open(prompt_path, 'r', encoding='utf-8') as f:
                self._templates = yaml.safe_load(f) or {}
        else:
            print(f"Warning: Prompt file not found at {prompt_path}")

    def get(self, key: str) -> str:
        return self._templates.get(key, "")

prompt_loader = PromptLoader()
