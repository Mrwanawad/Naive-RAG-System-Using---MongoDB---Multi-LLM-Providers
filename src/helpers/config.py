from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings( BaseSettings ):
    
    APP_NAME: str
    APP_VERSION: str
    ANTHROPIC_API_KEY: str
    
    FILE_ALLOWED_TYPES: list
    FILE_MAX_SIZE: int
    FILE_DEFAULT_CHUNK_SIZE: int
    
    MONGODB_URL: str
    MONGODB_DATABASE: str
    
    POSTGRES_USERNAME: str
    POSTGRES_PASSWORD: str
    POSTGRES_HOST: str
    POSTGRES_PORT: int
    POSTGRES_MAIN_DATABASE: str
        
    GENERATION_BACKEND: str
    EMBEDDING_BACKEND: str

    OPENAI_API_KEY: str = None
    OPENAI_BASE_URL: str = None

    COHERE_API_KEY: str = None

    GENERATION_MODEL_ID: str = None
    EMBEDDING_MODEL_ID: str = None
    EMBEDDING_MODEL_SIZE: int = None

    DEFAULT_INPUT_MAX_CHARACTERS: int = None
    GENERATION_DEFAULT_MAX_TOKENS: int = None
    GENERATION_DEFAULT_TEMPERATURE: float = None
    
    OPENROUTER_GENERATION_API_URL: str = None
    OPENROUTER_EMBEDDING_API_URL: str = None
    OPENROUTER_API_KEY: str = None
    OPENROUTER_GENERATION_MODEL: str = None
    OPENROUTER_EMBEDDING_MODEL: str = None
    
    VECTOR_DB_BACKEND: str = None
    VECTOR_DB_PATH: str = None
    VECTOR_DB_DISTANCE_METHOD: str = None
    
    PRIMARY_LANG: str="en"
    DEFAULT_LANG: str="en"

    model_config = SettingsConfigDict(env_file="../.env")
        
def get_settings() :
    
    return Settings()        


if __name__ == '__main__':
    
    try:
        s = get_settings()
        print( 'Initialized Settings Successfully !' )

        
    except Exception as e:
        print( f'Error Inititalizing app settings:\n{e}' )    