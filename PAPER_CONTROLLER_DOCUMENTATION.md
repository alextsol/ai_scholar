# Paper Controller Documentation

## Overview

The `PaperController` is a Flask-based controller that handles paper-related operations in the AI Scholar application. It provides REST API endpoints for aggregating, ranking, retrieving details, and comparing academic papers. This controller serves as the primary interface for paper management functionality within the system.

## Table of Contents

- [Class Structure](#class-structure)
- [Dependencies](#dependencies)
- [API Endpoints](#api-endpoints)
- [Methods Documentation](#methods-documentation)
- [Error Handling](#error-handling)
- [Authentication](#authentication)
- [Usage Examples](#usage-examples)

## Class Structure

```python
class PaperController:
    def __init__(self, paper_service: PaperService, ai_service: AIService)
```

### Constructor Parameters

- **`paper_service`** (`PaperService`): Service for paper-related operations
- **`ai_service`** (`AIService`): Service for AI-powered ranking and analysis

## Dependencies

The controller relies on the following imports and services:

- `Flask` components: `Blueprint`, `request`, `jsonify`
- `flask_login`: `current_user`, `login_required`
- Internal services: `PaperService`, `AIService`
- Data models: `SearchResult`, `SearchHistory`, `db`

## API Endpoints

The controller registers the following routes under the `/papers` URL prefix:

| Endpoint | Method | Description | Authentication |
|----------|--------|-------------|----------------|
| `/papers/aggregate` | POST | Aggregate and rank papers from multiple sources | Required |
| `/papers/rank` | POST | Rank a provided list of papers | Required |
| `/papers/<paper_id>/details` | GET | Get detailed information about a specific paper | Required |
| `/papers/compare` | POST | Compare multiple papers based on criteria | Required |

## Methods Documentation

### `aggregate_papers()`

**Purpose**: Aggregates papers from multiple sources and applies AI-powered ranking.

**HTTP Method**: POST

**Authentication**: Required (`@login_required`)

#### Request Body Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `query` | string | Yes | - | Search query for papers |
| `limit` | integer | No | 100 | Maximum number of papers to aggregate |
| `ai_result_limit` | integer | No | 10 | Number of top results to return after AI ranking |
| `ranking_mode` | string | No | "ai" | Ranking algorithm to use |
| `min_year` | integer | No | null | Minimum publication year filter |
| `max_year` | integer | No | null | Maximum publication year filter |

#### Response Format

**Success Response (200)**:
```json
{
  "success": true,
  "results": [...],
  "total_count": 150,
  "sources_used": ["arxiv", "semantic_scholar"],
  "ranking_applied": "ai",
  "search_time": 2.34
}
```

**Error Responses**:
- `400`: Missing data or empty query
- `500`: Aggregation operation failed

#### Functionality

1. Validates input parameters
2. Calls `paper_service.aggregate_and_rank_papers()` with provided parameters
3. Saves search history to database
4. Returns aggregated and ranked results with metadata

### `rank_papers()`

**Purpose**: Ranks a provided list of papers using AI-powered algorithms.

**HTTP Method**: POST

**Authentication**: Required (`@login_required`)

#### Request Body Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `papers` | array | Yes | - | List of papers to rank |
| `query` | string | Yes | - | Query context for ranking |
| `ranking_mode` | string | No | "ai" | Ranking algorithm to use |
| `limit` | integer | No | 10 | Number of top results to return |

#### Response Format

**Success Response (200)**:
```json
{
  "success": true,
  "ranked_papers": [...],
  "ranking_mode": "ai",
  "total_ranked": 10
}
```

**Error Responses**:
- `400`: Missing data, empty papers list, or missing query
- `500`: Ranking operation failed

#### Functionality

1. Validates input parameters (papers list and query)
2. Calls `ai_service.rank_papers()` with provided parameters
3. Returns ranked papers with ranking metadata

### `get_paper_details(paper_id)`

**Purpose**: Retrieves detailed information about a specific paper.

**HTTP Method**: GET

**Authentication**: Required (`@login_required`)

#### URL Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `paper_id` | string | Yes | Unique identifier of the paper |

#### Response Format

**Success Response (200)**:
```json
{
  "success": true,
  "paper": {
    "id": "paper_id",
    "title": "Paper Title",
    "authors": [...],
    "abstract": "...",
    ...
  }
}
```

**Error Responses**:
- `404`: Paper not found
- `500`: Failed to retrieve paper details

#### Functionality

1. Calls `paper_service.get_paper_details()` with the provided paper ID
2. Returns detailed paper information or appropriate error response

### `compare_papers()`

**Purpose**: Compares multiple papers based on specified criteria.

**HTTP Method**: POST

**Authentication**: Required (`@login_required`)

#### Request Body Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `papers` | array | Yes | - | List of papers to compare (minimum 2) |
| `criteria` | array | No | ["citations", "year", "relevance"] | Comparison criteria |

#### Response Format

**Success Response (200)**:
```json
{
  "success": true,
  "comparison": {
    "results": [...],
    "analysis": "..."
  },
  "criteria_used": ["citations", "year", "relevance"]
}
```

**Error Responses**:
- `400`: Missing data or insufficient papers (less than 2)
- `500`: Comparison operation failed

#### Functionality

1. Validates that at least 2 papers are provided
2. Calls `paper_service.compare_papers()` with papers and criteria
3. Returns comparison results with used criteria

### `_save_aggregation_history()` (Private Method)

**Purpose**: Saves aggregation search history to the database for user tracking.

#### Parameters

- `query` (string): Search query used
- `limit` (int): Result limit applied
- `ai_result_limit` (int): AI ranking limit applied
- `ranking_mode` (string): Ranking mode used
- `min_year` (Optional[int]): Minimum year filter
- `max_year` (Optional[int]): Maximum year filter
- `result` (SearchResult): Aggregation result object

#### Functionality

1. Creates a search parameters dictionary
2. Creates a `SearchHistory` record with user information
3. Commits the record to the database
4. Handles database rollback on errors

## Error Handling

The controller implements comprehensive error handling:

### Input Validation Errors (400)
- Missing request data
- Empty or missing required fields
- Invalid parameter values
- Insufficient data for operations

### Not Found Errors (404)
- Paper not found for detail requests

### Server Errors (500)
- Service operation failures
- Database operation failures
- Unexpected exceptions

### Error Response Format
```json
{
  "error": "Descriptive error message"
}
```

## Authentication

All endpoints require user authentication via Flask-Login:
- Uses `@login_required` decorator
- Accesses `current_user` for user identification
- Saves user-specific search history

## Usage Examples

### Aggregate Papers

```bash
curl -X POST http://localhost:5000/papers/aggregate \
  -H "Content-Type: application/json" \
  -d '{
    "query": "machine learning neural networks",
    "limit": 50,
    "ai_result_limit": 10,
    "ranking_mode": "ai",
    "min_year": 2020,
    "max_year": 2024
  }'
```

### Rank Papers

```bash
curl -X POST http://localhost:5000/papers/rank \
  -H "Content-Type: application/json" \
  -d '{
    "papers": [
      {"id": "paper1", "title": "Paper 1", ...},
      {"id": "paper2", "title": "Paper 2", ...}
    ],
    "query": "deep learning applications",
    "ranking_mode": "ai",
    "limit": 5
  }'
```

### Get Paper Details

```bash
curl -X GET http://localhost:5000/papers/12345/details
```

### Compare Papers

```bash
curl -X POST http://localhost:5000/papers/compare \
  -H "Content-Type: application/json" \
  -d '{
    "papers": [
      {"id": "paper1", ...},
      {"id": "paper2", ...}
    ],
    "criteria": ["citations", "year", "relevance"]
  }'
```

## Database Integration

The controller integrates with the database through:

- **SearchHistory Model**: Records user search activities
- **Database Session Management**: Handles commits and rollbacks
- **User Association**: Links search history to authenticated users

## Performance Considerations

- Implements result limiting to prevent large response payloads
- Uses pagination-friendly parameters (`limit`, `ai_result_limit`)
- Handles database transactions with proper error recovery
- Provides processing time metrics in responses

## Future Enhancements

Potential areas for improvement:

1. **Caching**: Implement response caching for frequently requested papers
2. **Async Processing**: Add support for long-running aggregation operations
3. **Batch Operations**: Support bulk paper operations
4. **Advanced Filtering**: Add more sophisticated search filters
5. **Export Functionality**: Add endpoints for exporting results in various formats

## Related Components

- **PaperService**: Core business logic for paper operations
- **AIService**: AI-powered ranking and analysis
- **SearchHistory**: Database model for tracking searches
- **SearchResult**: Data model for search results
- **Flask Blueprint**: Route registration and URL management
