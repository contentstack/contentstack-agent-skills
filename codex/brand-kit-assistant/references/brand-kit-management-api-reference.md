Operate Contentstack Brand Kit and Voice Profile APIs with correct headers, payloads, and safety checks. Use for list/get/create/update/delete operations, region-aware base URL selection, payload validation, and rate-limit handling.

## Safety
- Never expose Brand Kit API tokens or other secrets.
- Never delete Brand Kits.
- Require explicit user confirmation before deleting a Voice Profile.
- Validate generated or updated content against brand guidelines before presenting it as ready.
- Stop and ask for missing required IDs, headers, or region details.
- Treat 429 responses as rate-limit events and avoid aggressive retries.

## Inputs
- Operation type: list, get, create, update, delete
- Target resource: Brand Kit or Voice Profile
- Region / base URL
- organization_uid and authtoken
- brand_kit_uid for Voice Profile operations
- brand_kit_uid or voice_profile_uid for targeted get/update/delete operations
- Name, description, linked stack API keys, communication_style, insights, and sample content as needed

## Behavior
- Select the correct regional base URL.
- Include authtoken and organization_uid for Brand Kit endpoints.
- Include authtoken and brand_kit_uid for Voice Profile endpoints.
- Validate required IDs and payload fields before calling the API.
- For create/update, support brand_kit.name, optional brand_kit.description, and optional brand_kit.api_keys.
- For Voice Profiles, validate communication_style values are integers from 1 to 5 and include insights and sample_content when available.
- If deleting a Voice Profile, ask for explicit confirmation before proceeding.
- If the API returns 429, report rate-limit status and recommend retrying after a short delay.

## Output
Return concise, action-oriented results with the exact endpoint, headers, and JSON body when requested. Summarize validation issues, returned IDs, and changed fields clearly. Do not include secrets.