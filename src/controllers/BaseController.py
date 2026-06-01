import os
from helpers.config import get_settings, Settings

class BaseController:
    
    def __init__(self):
        self.app_settings = get_settings()
        self.base_dir = os.path.dirname( os.path.dirname( __file__ ) )
        self.file_dir = os.path.join( self.base_dir, "assets/files" )
        self.database_dir = os.path.join( self.base_dir, "assets/database" )
        
        
    def get_database_path(self, db_name: str):
        database_dir = os.path.join( self.database_dir, db_name ) 
        if not os.path.exists(database_dir):
            os.makedirs( database_dir )
            
        return database_dir       
