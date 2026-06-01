from enum import Enum


class LLMEnums(Enum):
    OPENAI = "openai"
    COHERE = "cohere"
    OPENROUTER = 'openrouter'

class OpenAIEnums(Enum):
    SYSTEM = 'system'
    USER = 'user'
    ASSISTANT = 'assistant'   
    


class CoHereEnums(Enum):
    SYSTEM = 'system'
    USER = 'user'
    ASSISTANT = 'assistant'
    
    DOCUMENT = 'search_document'
    QUERY = 'search_query'
    
    
class OpenRouterEnums(Enum):
    SYSTEM = 'system'
    USER = 'user'
    ASSISTANT = 'assistant'       

class DocumentTypeEnums(Enum):
    DOCUMENT = 'document'
    QUERY = 'query'