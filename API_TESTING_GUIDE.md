# InfiniGram API Testing Guide

## Overview
The InfiniGram API provides endpoints for document attribution and index management. This guide shows you how to test all available endpoints.

## Available Endpoints

### 1. Health Check
- **GET** `/health/` - Health check endpoint
- **Status**: 204 No Content (healthy)

### 2. Indexes
- **GET** `/indexes` - Get available indexes
- **Response**: List of available InfiniGram indexes

### 3. Attribution
- **POST** `/{index}/attribution` - Get document attributions for text (v1 format)
- **POST** `/{index}/attribution/v2` - Get document attributions for text (v2 format)
- **Parameters**: 
  - `index`: One of the available indexes
  - `body`: AttributionRequest with text and parameters

## Available Indexes
Based on the code, the following indexes are available:
- `pileval-llama`
- `olmoe-0125-1b-7b`
- `olmo-2-1124-13b`
- `olmo-2-0325-32b`
- `tulu-3-8b`
- `tulu-3-70b`
- `tulu-3-405b`

## Testing Commands

### 1. Health Check
```bash
curl -X GET "http://localhost:8080/health/" -v
```

### 2. Get Available Indexes
```bash
curl -X GET "http://localhost:8080/indexes" -H "accept: application/json"
```

### 3. Test Attribution (v1 format)
```bash
curl -X POST "http://localhost:8080/pileval-llama/attribution" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{
    "response": "The quick brown fox jumps over the lazy dog.",
    "delimiters": ["\n", ".", "!"],
    "allow_spans_with_partial_words": false,
    "minimum_span_length": 3,
    "maximum_frequency": 1000,
    "maximum_span_density": 0.5,
    "span_ranking_method": "frequency",
    "maximum_context_length": 100,
    "maximum_context_length_long": 200,
    "maximum_context_length_snippet": 50,
    "maximum_documents_per_span": 10
  }'
```

### 4. Test Attribution V2 (new format)
```bash
curl -X POST "http://localhost:8080/olmo-2-0325-32b/attribution/v2" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{
    "response": "Paris is the capital of France and one of the most visited cities in the world. It is known for its rich history, both culturally and politically, and it is one of the most visited cities in the world.",
    "delimiters": ["\n", ".", "!"],
    "allow_spans_with_partial_words": false,
    "minimum_span_length": 3,
    "maximum_frequency": 1000,
    "maximum_span_density": 0.5,
    "span_ranking_method": "frequency",
    "maximum_context_length": 100,
    "maximum_context_length_long": 200,
    "maximum_context_length_snippet": 50,
    "maximum_documents_per_span": 10
  }'
```

## Testing with Different Indexes

### Test with Olmo Index (v1)
```bash
curl -X POST "http://localhost:8080/olmoe-0125-1b-7b/attribution" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{
    "response": "Machine learning is a subset of artificial intelligence.",
    "delimiters": ["\n", ".", "!"],
    "allow_spans_with_partial_words": false,
    "minimum_span_length": 3,
    "maximum_frequency": 1000,
    "maximum_span_density": 0.5,
    "span_ranking_method": "frequency",
    "maximum_context_length": 100,
    "maximum_context_length_long": 200,
    "maximum_context_length_snippet": 50,
    "maximum_documents_per_span": 10
  }'
```

### Test with Olmo Index (v2)
```bash
curl -X POST "http://localhost:8080/olmoe-0125-1b-7b/attribution/v2" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{
    "response": "Machine learning is a subset of artificial intelligence.",
    "delimiters": ["\n", ".", "!"],
    "allow_spans_with_partial_words": false,
    "minimum_span_length": 3,
    "maximum_frequency": 1000,
    "maximum_span_density": 0.5,
    "span_ranking_method": "frequency",
    "maximum_context_length": 100,
    "maximum_context_length_long": 200,
    "maximum_context_length_snippet": 50,
    "maximum_documents_per_span": 10
  }'
```

### Test with Tulu Index (v2)
```bash
curl -X POST "http://localhost:8080/tulu-3-8b/attribution/v2" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{
    "response": "Natural language processing enables computers to understand human language.",
    "delimiters": ["\n", ".", "!"],
    "allow_spans_with_partial_words": false,
    "minimum_span_length": 3,
    "maximum_frequency": 1000,
    "maximum_span_density": 0.5,
    "span_ranking_method": "frequency",
    "maximum_context_length": 100,
    "maximum_context_length_long": 200,
    "maximum_context_length_snippet": 50,
    "maximum_documents_per_span": 10
  }'
```

## Expected Responses

### Health Check Response
- Status: 204 No Content
- No body content

### Indexes Response
```json
[
  "pileval-llama",
  "olmoe-0125-1b-7b",
  "olmo-2-1124-13b",
  "olmo-2-0325-32b",
  "tulu-3-8b",
  "tulu-3-70b",
  "tulu-3-405b"
]
```

### Attribution Response (v1 format)
```json
{
  "attributions": [
    {
      "span": "text span",
      "documents": [
        {
          "document_index": 123,
          "context": "context around the span",
          "context_long": "longer context",
          "context_snippet": "short snippet"
        }
      ]
    }
  ]
}
```

### Attribution Response V2 (new format)
```json
{
  "index": "olmo-2-0325-32b",
  "spans": [
    {
      "start_index": 12,
      "text": "both culturally and politically, and it is one of the most visited cities in the world.",
      "nested_spans": [],
      "documents": ["409657456", "329048572"]
    }
  ],
  "documents": [
    {
      "index": "409657456",
      "display_name": "olmo-mix-1124",
      "relevance_score": 33.6,
      "secondary_name": "web corpus (DCLM)",
      "corresponding_span_texts": ["landmarks such as the Eiffel Tower..."],
      "corresponding_spans": [0],
      "snippets": [
        {
          "text": "...Visit some of the city's most famous landmarks such as the Eiffel Tower..."
        }
      ],
      "text_long": "<full document text>",
      "title": null,
      "source": "dclm-hero-run-fasttext_for_HF",
      "source_url": "http://triptard.com/travel-guide/Paris",
      "usage": "Pre-training"
    }
  ]
}
```

## Error Handling

### Invalid Index
- Status: 404 Not Found
- Error message for non-existent index

### Invalid Request
- Status: 422 Unprocessable Entity
- Validation error details

### Timeout Error
- Status: 408 Request Timeout
- When attribution processing takes too long

## Testing Tips

1. **Start with health check** to ensure the API is running
2. **Check available indexes** to see which ones are accessible
3. **Test with different input lengths** to see how the API handles various text sizes
4. **Try different delimiters** to see how text segmentation affects results
5. **Monitor response times** to understand performance characteristics

## Troubleshooting

### Port Forwarding Issues
If port forwarding fails, check:
- Pod status: `kubectl get pods -l app=infinigram-api`
- Service status: `kubectl get services -l app=infinigram-api`
- Pod logs: `kubectl logs <pod-name> -c api`

### API Not Responding
Check:
- Container readiness: `kubectl describe pod <pod-name>`
- Health endpoint: `curl http://localhost:8080/health/`
- Service connectivity: `kubectl get endpoints infinigram-service` 