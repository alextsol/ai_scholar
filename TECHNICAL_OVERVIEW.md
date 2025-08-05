# AI Scholar - Technical Overview

*For Senior Engineers: Quick Technical Assessment*

## 🏗️ Architecture Overview

**Pattern**: MVC Architecture with Service Layer
**Stack**: Flask + SQLAlchemy + Bootstrap + Vanilla JS
**Python**: 3.11+

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Controllers   │───▶│    Services      │───▶│   Providers     │
│                 │    │                  │    │                 │
│ • SearchCtrl    │    │ • SearchService  │    │ • ArXiv         │
│ • PaperCtrl     │    │ • AIService      │    │ • Semantic      │
│ • WebCtrl       │    │ • PaperService   │    │ • CrossRef      │
│ • AdminCtrl     │    │                  │    │ • CORE          │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│     Models      │    │    Interfaces    │    │   AI Providers  │
│                 │    │                  │    │                 │
│ • User          │    │ • ISearchProvider│    │ • Google Gemini │
│ • SearchHistory │    │ • IAIProvider    │    │ • OpenRouter    │
│ • Paper         │    │ • ICacheProvider │    │                 │
│ • SearchRequest │    │ • IRankingProvider│   │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## 🚀 Entry Points

| File | Purpose |
|------|---------|
| `main.py` | Application entry point |
| `passenger_wsgi.py` | WSGI production entry |
| `ai_scholar/app_factory.py` | Flask app factory with dependency injection |

## 📁 Core Directory Structure

```
ai_scholar/
├── controllers/          # HTTP request handlers
│   ├── search_controller.py
│   ├── paper_controller.py
│   ├── web_controller.py
│   └── admin_controller.py
├── services/            # Business logic layer
│   ├── search_service.py
│   ├── ai_service.py
│   ├── paper_service.py
│   └── service_factory.py
├── providers/           # External API integrations
│   ├── arxiv_search_provider.py
│   ├── semantic_scholar_provider.py
│   ├── crossref_provider.py
│   ├── core_provider.py
│   ├── opencitations_provider.py
│   └── ai/
│       ├── openrouter_provider.py
│       └── gemini_provider.py
├── models/              # Data models & database
│   ├── database.py      # SQLAlchemy models
│   ├── paper.py
│   ├── search_request.py
│   └── search_result.py
├── interfaces/          # Abstract contracts
│   ├── search_interface.py
│   ├── ai_interface.py
│   └── cache_interface.py
├── utils/               # Utilities & helpers
│   ├── exceptions.py
│   ├── error_handler.py
│   ├── validators.py
│   └── ai_utils.py
└── config/              # Configuration management
    ├── settings.py
    ├── database_config.py
    └── providers_config.py
```

## 🔌 External Integrations

### Academic Search Providers
- **ArXiv** - Preprint repository (no API key required)
- **Semantic Scholar** - AI-powered academic search (requires API key)
- **CrossRef** - DOI and citation database (no API key required)
- **CORE** - Open access repository (requires API key)
- **OpenCitations** - Citation analysis and bibliometric data (no API key required)

### AI Providers
- **Google Gemini** - Primary AI for ranking and analysis
- **OpenRouter** - Fallback AI provider (multiple models)

### Database
- **SQLite** - Default development database
- **PostgreSQL/MySQL** - Production ready (configurable)

## 🔑 Key Components

### Service Layer (`services/`)
```python
# Orchestrates multi-provider searches
SearchService.unified_search(query, providers, ai_enabled)

# Handles AI operations (ranking, summarization)
AIService.rank_papers(papers, query, criteria)

# Paper processing and deduplication
PaperService.process_papers(raw_results)
```

### Provider Layer (`providers/`)
```python
# All providers implement ISearchProvider interface
class ArxivSearchProvider(ISearchProvider):
    def search(self, query: str, max_results: int) -> List[Paper]
    def get_paper_details(self, paper_id: str) -> Paper
```

### Controllers (`controllers/`)
```python
# REST API endpoints
SearchController.api_search()  # POST /search/api
PaperController.get_paper()    # GET /paper/<id>
WebController.index()          # GET /
```

## 📊 Database Schema

```sql
-- Core entities
users (id, username, email, password_hash, created_at)
search_history (id, user_id, query, results_count, created_at)

-- No persistent paper storage (real-time fetching)
```

## ⚙️ Configuration

### Environment Variables
```bash
# Required
DATABASE_URL=sqlite:///instance/scholar_search.db
SECRET_KEY=your-secret-key

# API Keys (optional but recommended)
SEMANTIC_SCHOLAR_API_KEY=your-key
CORE_API_KEY=your-key
GOOGLE_API_KEY=your-key
OPENROUTER_API_KEY=your-key
```

### Config Hierarchy
1. Environment variables
2. `config.py` (development defaults)
3. `ai_scholar/config/settings.py` (new architecture)

## 🔄 Request Flow

```
1. User submits search → WebController
2. WebController → SearchController.api_search()
3. SearchController → SearchService.unified_search()
4. SearchService → Multiple providers (parallel)
5. PaperService.process_papers() → Deduplication
6. AIService.rank_papers() → AI ranking (if enabled)
7. Results → JSON response → Frontend JavaScript
```

## 🧪 Testing Structure

```
tests/
├── unit/           # Unit tests for services/providers
├── integration/    # API endpoint tests
└── fixtures/       # Test data
```

## 🚀 Deployment

### Development
```bash
python main.py  # Runs on localhost:5000
```

### Production
- Uses `passenger_wsgi.py` for WSGI deployment
- Database migrations via `migrate_db.py`
- Static files served from `static/`

## 🔍 Key Files to Examine

For quick understanding, focus on these files:

1. **Architecture**: `ai_scholar/app_factory.py`
2. **Search Logic**: `ai_scholar/services/search_service.py`
3. **API Endpoints**: `ai_scholar/controllers/search_controller.py`
4. **Data Models**: `ai_scholar/models/database.py`
5. **Provider Implementation**: `ai_scholar/providers/arxiv_search_provider.py`
6. **Frontend Logic**: `static/js/` (search.js, result-filter.js)

## 🐛 Common Issues & Solutions

### Database Issues
```bash
python recreate_db.py  # Reset database
python migrate_db.py   # Apply migrations
```

### API Rate Limits
- Implemented in `providers/` with tenacity retry logic
- Graceful fallback when providers fail

### Missing Dependencies
```bash
pip install -r requirements.txt
```

## 📈 Performance Considerations

- **Parallel Searches**: Multiple providers called simultaneously
- **Caching**: Response caching for repeated queries (configurable)
- **Rate Limiting**: Built-in API rate limit handling
- **Deduplication**: Efficient paper deduplication algorithm
- **Lazy Loading**: Frontend pagination and filtering

## 🔧 Extension Points

- **New Providers**: Implement `ISearchProvider` interface
- **New AI Models**: Implement `IAIProvider` interface
- **Custom Ranking**: Extend `IRankingProvider`
- **New Controllers**: Follow MVC pattern in `controllers/`

---

*This overview covers the essential technical aspects needed to understand and work with the AI Scholar codebase.*
