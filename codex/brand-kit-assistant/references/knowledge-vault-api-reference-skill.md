Operate Contentstack Knowledge Vault through the API and mapped MCP tools with region-aware endpoints, required headers, payload validation, and safe write/delete handling. Support ingest, list, get, update, delete, and chunk retrieval while staying within Knowledge Vault capabilities.

## Safety
- Never expose Brand Kit API tokens or other secrets.
- Require explicit user confirmation before deleting Knowledge Vault content.
- Treat Knowledge Vault as a vector store for extracted knowledge, not a document repository.
- Do not imply original-file retrieval or binary asset access.
- Stop and ask for missing required IDs, headers, region details, or content fields.
- Treat 429 responses as rate-limit events and avoid aggressive retries.

## Inputs
- Operation type: ingest/add, list, get, update, delete, get chunks, or MCP-mapped equivalent
- Region / base URL
- brand_kit_uid
- content_uid for get, update, or delete
- Content text to ingest or update
- Optional metadata such as title, category, date, or external ID

## Behavior
- Select the correct regional base URL.
- Include authtoken and brand_kit_uid headers.
- Validate required IDs and payload fields before calling the API.
- Accept text intended for semantic storage and include useful metadata when available.
- For delete, request explicit confirmation and verify brand_kit_uid and content_uid before proceeding.
- If the API returns 429, report rate-limit status and recommend retrying after a short delay.
- Support mapped MCP operations where available.

## Output
Return concise, action-oriented results with the exact endpoint, headers, and JSON body when requested. Summarize validation issues, returned IDs, and changed fields clearly. Do not include secrets.