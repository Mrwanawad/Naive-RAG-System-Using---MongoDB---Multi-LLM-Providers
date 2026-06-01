from ..LLMInterface import LLMInterface
from ..LLMEnums import OpenRouterEnums
import requests
import json
import logging


class OpenRouterProvider( LLMInterface ):
    
    def __init__(self,  api_key: str, generation_api_url: str=None, embedding_api_url: str=None,
                 default_input_max_characters: int=1000,
                 default_generation_max_output_tokens: int=1000,
                 default_generation_temperature: float=0.1
                 ):
        self.api_key = api_key
        self.generation_api_url = generation_api_url
        self.embedding_api_url = embedding_api_url
        self.default_input_max_characters = default_input_max_characters
        self.default_generation_max_output_tokens = default_generation_max_output_tokens
        self.default_generation_temperature = default_generation_temperature
        
        self.generation_model_id = None
        
        self.embedding_model_id = None
        self.embedding_size = None
        
        self.enums = OpenRouterEnums
        self.logger = logging.getLogger( __name__ )
        

    def set_generation_model(self, model_id: str):
        self.generation_model_id = model_id

    def set_embedding_model(self, model_id: str, embedding_size: int):
        self.embedding_model_id = model_id
        self.embedding_size = embedding_size

    def process_text(self, text: str):
        return text[:self.default_input_max_characters].strip()

    def generate_text(self, prompt: str, chat_history: list=[], max_output_tokens: int=None,
                            temperature: float = None):

        if not self.generation_model_id:
            self.logger.error("Generation model for OpenRouter.ai was not set")
            return None
        
        max_output_tokens = max_output_tokens if max_output_tokens else self.default_generation_max_output_tokens
        temperature = temperature if temperature else self.default_generation_temperature
        
        chat_history.append(
            self.construct_prompt(prompt=prompt, role= OpenRouterEnums.USER.value)
        )

        response = requests.post(
        url=self.generation_api_url,
        headers={
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        },
        data=json.dumps({
            "model": self.generation_model_id,
            "messages": chat_history,
            "max_tokens": max_output_tokens,     
            "temperature": temperature,           
            "max_input_tokens": self.default_input_max_characters, 
            
        })
        )

        response = response.json()
                  
        if not response or 'error' in list( response.keys() ):
            self.logger.error("Error while generating text with OpenRouter.ai")
            return None
        
        return response['choices'][0]['message']['content']
    
    
    
    def embed_text(self, text: str, document_type: str="search_document"):

        
        if not self.embedding_model_id:
            
            self.logger.error("Embedding model for OpenRouter.ai was not set")
            return None

        response = requests.post(
        url=self.embedding_api_url,
        headers={
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        },
        data=json.dumps({
            "model": self.embedding_model_id,
            "input": [
            {
                "content": [
                {"type": "text", "text": text},
                ]
            }
            ],
            "encoding_format": "float",
            "dimensions": self.embedding_size
        })
        )

        if not response.json()['data'][0]['embedding']:
            self.logger.error("Error while embedding text with OpenRouter.ai")
            return None
        
        self.logger.info(" Embedded text with OpenRouter.ai Sucess")
        return response.json()['data'][0]['embedding']
    
    def construct_prompt(self, prompt: str, role: str):
        return {
            "role": role,
            "content": self.process_text(prompt)
        }
    
