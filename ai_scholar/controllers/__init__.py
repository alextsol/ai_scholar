from typing import Dict
from flask import Flask
from .search_controller import SearchController
from .paper_controller import PaperController
from .web_controller import WebController
from .history_controller import HistoryController
from .history_controller import HistoryController

class ControllerRegistry:
    
    def __init__(self):
        self.controllers: Dict[str, object] = {}
        self._initialized = False
    
    def initialize_controllers(self, app: Flask, **services):
        if self._initialized:
            return
        
        search_service = services.get('search_service')
        paper_service = services.get('paper_service')
        ai_service = services.get('ai_service')
        
        if search_service:
            self.controllers['search'] = SearchController(search_service)
        
        if paper_service and ai_service:
            self.controllers['paper'] = PaperController(paper_service, ai_service)
        
        if search_service and paper_service:
            self.controllers['web'] = WebController(search_service, paper_service)
        
        self.controllers['history'] = HistoryController()
        
        self._register_blueprints(app)
        
        self._initialized = True
    
    def _register_blueprints(self, app: Flask):
        """Register all controller blueprints with the Flask app"""
        for name, controller in self.controllers.items():
            if hasattr(controller, 'blueprint'):
                app.register_blueprint(controller.blueprint)
    
    def get_controller(self, name: str):
        return self.controllers.get(name)
    
    def get_all_controllers(self) -> Dict[str, object]:
        return self.controllers.copy()
    
    def is_initialized(self) -> bool:
        return self._initialized

controller_registry = ControllerRegistry()
