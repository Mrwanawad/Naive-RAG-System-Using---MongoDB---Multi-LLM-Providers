from pydantic import BaseModel, Field, field_validator
from typing import Optional
from bson.objectid import ObjectId



class Project( BaseModel ):
    
    id: Optional[str] = Field(None, alias="_id")  # maps MongoDB's _id → id
    project_id: str = Field( ..., min_length= 1 )
    
    @field_validator('project_id')
    def validate_project_id( cls, value ):
        if not value.isalnum():
            raise ValueError( 'Project ID must be alphanumeric' )
        
        return value
    
    class Config:
        arbitrary_types_allowed= True
        populate_by_name = True  # allows using both 'id' and '_id'  
        json_encoders = {
            ObjectId: str
        }
        
        
    @classmethod
    def get_indexex( cls):
        
        return [
            {
                'key': [
                    ( 'project_id', 1 )
                ],
                'name': "project_id_index_1",
                'unique': True 
            }
        ]    