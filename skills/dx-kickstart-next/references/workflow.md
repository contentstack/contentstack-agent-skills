# Workflow guidance for kickstart-next

Use this for setup, seeding, environment variables, validation commands, CI expectations, docs updates, dependency changes, or PR prep.

## Local setup

- Prefer npm: install with `npm install`.
- Copy `.env.example` to `.env` and fill in Contentstack values locally.
- Run the app with `npm run dev`, then open `http://localhost:3000`.
- For production verification, run `npm run build` and then `npm run start` if runtime behavior needs manual checking.

## Contentstack stack setup

- Install the Contentstack CLI with `npm install -g @contentstack/cli` if the user needs to seed a stack.
- Configure the CLI region when prompted; free developer accounts are commonly EU, but verify the user's account/URL.
- Login with `csdx auth:login`.
- Seed the compatible model with `csdx cm:stacks:seed --repo "contentstack/kickstart-stack-seed" --org "<YOUR_ORG_ID>" -n "Kickstart Stack"`.
- Create a delivery token with preview scope and a preview token when Live Preview is needed.
- Enable Live Preview in the stack settings for the preview environment.

## Validation

- After JavaScript or TypeScript edits, run `npm run build`.
- Run `npm run lint` when the script exists.
- Run `npm run typecheck` only if `package.json` defines it.
- Run tests only if the checkout defines test scripts or test tooling. The upstream kickstart currently has no default `test` script.
- If validation cannot run because Contentstack credentials are unavailable, report that clearly and still run static checks that do not require credentials.

## Environment and docs

- When adding or renaming environment variables, update `.env.example` and user-facing setup docs together.
- Document runtime behavior changes in `docs/` when the repository has or needs product-facing docs for that behavior.
- Keep README setup snippets short and copyable.
- Never commit real API keys, delivery tokens, preview tokens, management tokens, organization IDs, or stack IDs.

## CI expectations

- Verify `.github/workflows` before making CI claims.
- Upstream workflows focus on security/policy checks such as Snyk/SCA, security policy/license checks, and issue-to-Jira integration.
- Do not assume GitHub Actions runs `npm run build`, `npm run lint`, unit tests, or E2E tests unless a workflow in the checkout proves it.

## Ownership and dependencies

- Check `.github/CODEOWNERS` before making reviewer or ownership claims.
- Dependency changes can affect Snyk/SCA workflows; keep package lock changes intentional and explain why a dependency is needed.
- Prefer npm for dependency installation and lockfile updates.
