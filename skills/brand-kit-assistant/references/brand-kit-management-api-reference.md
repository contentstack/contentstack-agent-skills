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
- brand_kit_uid (path parameter) for Voice Profile operations
- brand_kit_uid or voice_profile_uid for targeted get/update/delete operations
- Name, description, linked stack API keys, communication_style, insights, and sample content as needed

## Behavior
- Select the correct regional base URL.
- Include authtoken and organization_uid for Brand Kit endpoints.
- Include authtoken and organization_uid for Voice Profile endpoints too, with brand_kit_uid in the path (`brand-kits/{brand_kit_uid}/voice-profiles`).
- Check whether the kit is v1 or v2. The API version is a request header. v2 kits use markdown profiles ("Documents"), and v1 voice-profile routes return `410 Gone` for them.
- Validate required IDs and payload fields before calling the API.
- For create/update, support brand_kit.name, optional brand_kit.description, and optional brand_kit.api_keys.
- For v1 Voice Profiles, validate the four communication_style dials (formality, tone, humor, complexity) are integers from 1 to 4, and include insights and sample_content when available.
- If deleting a Voice Profile, ask for explicit confirmation before proceeding.
- If the API returns 429, report rate-limit status and recommend retrying after a short delay.

## Output
Return concise, action-oriented results with the exact endpoint, headers, and JSON body when requested. Summarize validation issues, returned IDs, and changed fields clearly. Do not include secrets.