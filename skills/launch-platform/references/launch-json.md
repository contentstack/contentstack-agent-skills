# launch.json reference

`launch.json` sits at the repository root. Launch evaluates it at the edge before Edge Functions and the cache.

Order of evaluation:

1. `redirects`, top to bottom
2. `rewrites`, top to bottom
3. Edge Function (`functions/[proxy].edge.js`), if no rule matched
4. CDN cache lookup
5. Origin

## Redirects

Fields: `source`, `destination`, `statusCode` and optional `response.headers`. There is no `permanent` flag; use the status code. `301` and `308` are permanent, `302` and `307` temporary (`307` and `308` keep the HTTP method). The default is `308`.

```json
{
  "redirects": [
    {
      "source": "/old-blog/:slug",
      "destination": "/blog/:slug",
      "statusCode": 301,
      "response": {
        "headers": { "x-redirected-by": "launch" }
      }
    }
  ]
}
```

## Rewrites

Fields: `source`, `destination`, optional `request.headers` (added before the request reaches the destination) and `response.headers`. The browser URL does not change.

```json
{
  "rewrites": [
    {
      "source": "/api/partner/:path(.*)",
      "destination": "https://api.partner.example.com/:path",
      "response": {
        "headers": { "cache-control": "no-store" }
      }
    }
  ]
}
```

Don't put secrets in `request.headers`: `launch.json` is committed to the repository. Inject secrets from an Edge Function that reads environment variables instead.

## Patterns

Sources use `path-to-regexp` syntax:

- Named parameter: `/blog/:slug` → `/posts/:slug`
- Constrained parameter: `/category/:name(shoes|bags)`
- Catch-all: `/old/:path(.*)`. There is no bare `*` wildcard.
- Exclusions: `/:path((?!blog|docs).+)`

Rules run top to bottom, so put catch-all rules last.

## Cache priming

```json
{
  "cache": {
    "cachePriming": {
      "urls": ["/", "/blog", "/pricing"]
    }
  }
}
```

Launch requests these paths through the CDN after a deployment goes live. Up to 50 literal relative paths; no wildcards.

## Rules of thumb

- Sources are relative paths only, with no hostname.
- Escape a literal `?` as `\?`. Hash fragments (`#`) are not supported.
- Keep the file small (under about 200 KB). Move complex or data-driven routing into an Edge Function.
- Not supported in a monorepo sub-app; the file must be at the repository root.
