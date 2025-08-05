# Refactoring TODO

## Methods to Remove

### PaperController

#### `get_paper_details(self, paper_id: str)`
- Location: `ai_scholar/controllers/paper_controller.py`
- Issue: Depends on `paper_service.get_paper_details()` which currently returns `None`
- Status: **REMOVED** - Method has no value and underlying service method is not implemented

### WebController

#### `results(self)`
- Location: `ai_scholar/controllers/web_controller.py`
- Issue: Placeholder method that only returns `{'message': 'Results endpoint'}`
- Status: **REMOVED** - No functionality implemented

## Other TODOs

add enum to aggregate or regular

create new controller for history and move the methods from web_controller, and also move helper methods to other file instead 
of web_controller

def user_stats():
should be moved from auth