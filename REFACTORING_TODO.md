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

## Completed Refactoring

### ✅ Enum Implementation
- **Created**: `ai_scholar/enums/` module with separate files for different enum types
- **Files**:
  - `ai_scholar/enums/search_modes.py` - SearchMode, RankingMode enums  
  - `ai_scholar/enums/providers.py` - ProviderType, AIProviderType enums
  - `ai_scholar/enums/__init__.py` - Module initialization
- **Updated**: Services to use enums instead of hardcoded strings
  - `PaperService` now uses `ProviderType` and `RankingMode` enums
  - `SearchService` now uses `ProviderType` enum  
  - `ServiceFactory` now uses `ProviderType` enum
- **Benefits**: Type safety, better maintainability, prevents typos

### ✅ History Controller Migration  
- **Created**: `ai_scholar/controllers/history_controller.py`
- **Moved methods from WebController**:
  - `history()` - Display search history page
  - `delete_history_item()` - Delete specific history item
  - `clear_history_api()` - Clear all user history
- **Added**: `user_stats()` API endpoint (moved from auth)
- **Updated**: Controller registry to include HistoryController
- **Benefits**: Better separation of concerns, cleaner code organization

### ✅ Helper Methods Extraction
- **Created**: `ai_scholar/utils/web_helpers.py`
- **Moved methods from WebController**:
  - `group_results_by_source()` - Group search results by provider
  - `parse_int()` - Parse integer with fallback
  - `save_search_history()` - Save search to database
  - `get_user_stats()` - Get user statistics (moved from auth)
- **Updated**: WebController to use WebHelpers class
- **Benefits**: Reusable utilities, cleaner controller code

### ✅ User Stats Migration
- **Moved**: `user_stats()` function from `auth.py` to `WebHelpers.get_user_stats()`
- **Updated**: Route moved from `/auth/api/user-stats` to `/api/user-stats` (handled by HistoryController)
- **Benefits**: Better logical placement, consistent with data ownership

### ✅ Testing Implementation
- **Created**: `test_refactoring.py` with comprehensive tests
- **Created**: `test_route_registration.py` to verify Flask routes  
- **Test Coverage**:
  - Enum functionality and validation
  - WebHelpers utility methods
  - HistoryController initialization
  - User statistics functionality
  - Flask route registration and URL building
- **Status**: All tests passing ✅

### ✅ Template Updates
- **Updated**: `templates/components/navbar.html` - Fixed history route reference
- **Updated**: `templates/history.html` - Updated pagination routes
- **Updated**: `templates/history_new.html` - Updated pagination routes
- **Result**: All templates now correctly reference `history.history` instead of `web_main.history`

## Architecture Improvements

The refactoring has improved the application architecture in several ways:

1. **Type Safety**: Enums prevent runtime errors from typos in provider/mode strings
2. **Separation of Concerns**: History logic separated from general web logic
3. **Code Reusability**: Helper methods can be used across different controllers
4. **Maintainability**: Cleaner, more organized code structure
5. **Testability**: Better unit test coverage for individual components

## Updated File Structure

```
ai_scholar/
├── enums/
│   ├── __init__.py          # ✅ NEW
│   ├── search_modes.py      # ✅ NEW 
│   └── providers.py         # ✅ NEW
├── controllers/
│   ├── history_controller.py # ✅ NEW
│   ├── web_controller.py    # ✅ UPDATED (methods moved out)
│   └── ...
├── utils/
│   ├── web_helpers.py       # ✅ NEW
│   └── ...
├── services/
│   ├── paper_service.py     # ✅ UPDATED (uses enums)
│   ├── search_service.py    # ✅ UPDATED (uses enums)
│   └── ...
└── endpoints/
    └── auth.py              # ✅ UPDATED (user_stats removed)
```