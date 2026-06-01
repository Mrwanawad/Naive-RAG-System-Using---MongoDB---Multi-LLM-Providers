
from pydantic import BaseModel, Field, field_validator
from typing import Optional
from bson.objectid import ObjectId
from datetime import timezone, datetime

class Asset( BaseModel ):
    id: Optional[ObjectId] = Field(None, alias= '_id')
    asset_project_id: ObjectId
    asset_type:str = Field(..., min_length= 1)
    asset_name: str = Field(..., min_length= 1)
    asset_size: int = Field( ge= 0, default= None )
    asset_pushed_at: datetime = Field( default= timezone.utc )
    
    class Config:
        arbitrary_types_allowed= True
        json_encoders = {
            ObjectId: str
        }        
        
    @classmethod
    def get_indexex( cls ):
        
        return [
            {
                'key': [
                    ( 'chunk_project_id', 1 )
                ],
                'name': "chunk_project_id_index_1",
                'unique': False 
            },
            
            {
                'key': [
                    ('asset_project_id', 1),
                    ('asset_name', 1)
                    
                ],
                'name': 'asset_project_id_name_index_1',
                'unique': True
            }
        ]         