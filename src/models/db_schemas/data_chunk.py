from pydantic import BaseModel, Field, field_validator
from bson.objectid import ObjectId
from typing import Optional, Dict

class DataChunk( BaseModel ):
    id: Optional[ObjectId] = Field(None, alias="_id")
    chunk_text: str = Field( ..., min_length= 1 )
    chunk_metadata: Dict
    chunk_order: int = Field( ..., ge= 0 )
    chunk_project_id: ObjectId
    
    
    
    class Config:
        arbitrary_types_allowed= True
        populate_by_name = True
        json_encoders = {
            ObjectId: str
        }
        
    @classmethod
    def get_indexex( cls):
        
        return [
            {
                'key': [
                    ( 'chunk_project_id', 1 )
                ],
                'name': "chunk_project_id_index_1",
                'unique': False 
            }
        ]            

class RetrievelDocument(BaseModel):
    text: str
    score: float