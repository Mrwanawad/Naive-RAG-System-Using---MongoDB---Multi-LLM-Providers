import os
from fastapi import FastAPI
from contextlib import asynccontextmanager
from routes import base_router, data_router, vector_store_router
from helpers.config import get_settings
from motor.motor_asyncio import AsyncIOMotorClient
from stores.llm import LLMProviderFactory
from stores.vectordb import VectorDBProviderFactory
from stores.llm.system_templates import TemplateParser


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    app.mongo_conn = AsyncIOMotorClient( host = settings.MONGODB_URL )
    app.db_client = app.mongo_conn[ settings.MONGODB_DATABASE ]
    
    llm_provider_factory = LLMProviderFactory( config= settings )
    
    app.generation_client = llm_provider_factory.create( provider= settings.GENERATION_BACKEND )
    app.generation_client.set_generation_model( model_id= settings.GENERATION_MODEL_ID )
    
    app.embedding_client = llm_provider_factory.create( provider= settings.EMBEDDING_BACKEND )
    app.embedding_client.set_embedding_model( model_id= settings.EMBEDDING_MODEL_ID, embedding_size= settings.EMBEDDING_MODEL_SIZE )
    
    app.vector_db_client = VectorDBProviderFactory().create( provider= settings.VECTOR_DB_BACKEND )
    app.vector_db_client.connect()
    
    app.template_parser = TemplateParser(
        language= settings.PRIMARY_LANG,
        default_language= settings.DEFAULT_LANG
        
    )
    
    yield
    app.mongo_conn.close() 
    app.vector_db_client.disconnect()
    

# uvicorn main:app --reload
app = FastAPI(
    title= get_settings().APP_NAME,
    description= 'mini-rag app', 
    version= get_settings().APP_VERSION,
    lifespan= lifespan
)


       
    

app.include_router( base_router )
app.include_router( data_router )
app.include_router( vector_store_router )
