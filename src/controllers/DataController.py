import os
from .BaseController import BaseController
from .ProjectCntroller import ProjectController
from fastapi import UploadFile
from models.enums import ResponseSignal
from typing import Tuple
import string
import random
import re

class DataController( BaseController ):
    
    def __init__(self):
        super().__init__()
        self.size_scale = 1048576 # Convert MB to bytes
        
    def validate_uploaded_file( self, file: UploadFile ) -> Tuple[ bool, str ] :
        
        if file.content_type not in self.app_settings.FILE_ALLOWED_TYPES:
            return False, ResponseSignal.FILE_TYPE_NOT_SUPPORTED.value
        
        if file.size > self.app_settings.FILE_MAX_SIZE * self.size_scale :
            return False, ResponseSignal.FILE_SIZE_EXCEEDED.value
        
        else:   return True, ResponseSignal.FILE_VALIDATED_SUCCESS.value  


    def gen_random_string( self, length: int = 5 ):
        return ''.join( random.choices( string.ascii_lowercase + string.digits, k = length ) )

    def get_clean_filename( self, orig_file_name: str ) -> Tuple[str, str]:
        cleaned_file_name = re.sub( r'[^\w.]', '', orig_file_name.strip() )
        cleaned_file_name = cleaned_file_name.replace( " ", "_" )
        return cleaned_file_name

    def gen_unique_filename( self, orig_file_name: str, project_id: str ):
        random_filename = self.gen_random_string()
        project_path = ProjectController().get_project_path( project_id= project_id )
        
        cleaned_file_name = self.get_clean_filename( orig_file_name= orig_file_name )
        new_file_path = os.path.join(
            project_path,
            random_filename + "_" + cleaned_file_name
        )
        
        return new_file_path, random_filename + '_' + cleaned_file_name