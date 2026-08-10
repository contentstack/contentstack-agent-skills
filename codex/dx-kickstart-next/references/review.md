# Review guidance for kickstart-next

Use this for PR reviews, pre-PR checks, risk assessment, or summarizing changes for maintainers.

## Review stance

- Lead with bugs, regressions, missing validation, and security risks.
- Ground findings in file and line references when reviewing a local checkout.
- Separate blockers, major issues, and minor nits.
- Keep summaries secondary to findings.

## Blockers

- Secrets or real Contentstack credentials committed anywhere.
- Build or lint failures caused by the change.
- Broken production home route or preview route.
- Live Preview or Visual Builder field binding regressions.
- XSS regression from unsanitized rich text or unsafe `dangerouslySetInnerHTML`.
- Content type UID, field UID, or modular block changes that are not reflected in types/renderers/docs.

## Major issues

- New environment variables missing from `.env.example` or setup docs.
- New remote image hostnames not represented in `next.config.mjs`.
- Moving Contentstack setup out of `lib/contentstack.ts` without a clear simplification.
- Client-only preview code introduced into server execution paths.
- Dependency additions that are unnecessary for a minimal kickstart or likely to fail security scans.
- CI claims that do not match `.github/workflows`.

## Minor issues

- Overly complex abstractions in example code.
- Copy or README changes that make setup less direct.
- Styling changes that distract from the kickstart's purpose as a minimal Contentstack integration example.
- Type looseness where existing Contentstack types could be extended cleanly.

## Pre-PR checklist

- Run `npm run build`.
- Run `npm run lint` if present.
- Run any `typecheck` or `test` scripts only if present.
- Verify `.env.example` and docs for env changes.
- Scan the diff for secrets.
- Read `references/content-model.md` for schema-impacting changes.
- Check preview behavior if data fetching, CSLP `$` attributes, components, content model fields, or Live Preview initialization changed.
