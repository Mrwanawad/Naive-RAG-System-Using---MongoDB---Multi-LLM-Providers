from helpers.config import get_settings
from .LLMEnums import LLMEnums
from .providers import CoHereProvider, OpenAIProvider, OpenRouterProvider
from openai import OpenAI
OpenAI()

class LLMProviderFactory:
    
    def __init__(self, config = get_settings()):
        self.config = config
        
    def create(self, provider: str): 
        if provider == LLMEnums.OPENAI.value:
            return OpenAIProvider(
                api_key= self.config.OPENAI_API_KEY,
                base_url= self.config.OPENAI_BASE_URL,
                default_input_max_characters= self.config.DEFAULT_INPUT_MAX_CHARACTERS,
                default_generation_max_output_tokens= self.config.GENERATION_DEFAULT_MAX_TOKENS,
                default_generation_temperature= self.config.GENERATION_DEFAULT_TEMPERATURE
            )
        
        if provider == LLMEnums.COHERE.value:
            return CoHereProvider(
                api_key= self.config.COHERE_API_KEY
            )
            
        if provider == LLMEnums.OPENROUTER.value:
            return OpenRouterProvider(
                api_key= self.config.OPENROUTER_API_KEY,
                generation_api_url= self.config.OPENROUTER_GENERATION_API_URL,
                embedding_api_url= self.config.OPENROUTER_EMBEDDING_API_URL,
                
            )      