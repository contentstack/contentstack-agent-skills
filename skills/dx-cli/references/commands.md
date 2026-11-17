# csdx commands by plugin (CLI 2.x)

Bundled plugins ship with `@contentstack/cli`. Installable plugins need `csdx plugins:install <package>`. Run `csdx <command> --help` for the full flag list.

## Bundled

| Plugin | Commands |
| --- | --- |
| `@contentstack/cli-auth` | `auth:login` (`login`; `--oauth` for SSO), `auth:logout` (`logout`), `auth:whoami` (`whoami`), `auth:tokens:add`, `auth:tokens:list`, `auth:tokens:remove` |
| `@contentstack/cli-config` | `config:set:region`, `config:get:region`, `config:set:base-branch`, `config:get:base-branch`, `config:set:rate-limit`, `config:set:proxy`, `config:set:log`, `config:set:early-access-header` (and matching `get`/`remove` commands) |
| `@contentstack/cli-cm-export` | `cm:stacks:export` |
| `@contentstack/cli-cm-import` | `cm:stacks:import` |
| `@contentstack/cli-cm-seed` | `cm:stacks:seed` |
| `@contentstack/cli-cm-bootstrap` | `cm:bootstrap` (start a project from a starter app) |
| `@contentstack/cli-cm-clone` | `cm:stacks:clone` |
| `@contentstack/cli-cm-export-to-csv` | export entries, taxonomies, terms and organization users to CSV |
| `@contentstack/cli-migration` | `cm:stacks:migration` |
| `@contentstack/cli-cm-branches` | `cm:branches`, `cm:branches:create`, `cm:branches:delete`, `cm:branches:diff`, `cm:branches:merge`, `cm:branches:merge-status` |
| `@contentstack/cli-audit` | `cm:stacks:audit`, `cm:stacks:audit:fix` |
| `@contentstack/cli-bulk-operations` | `cm:stacks:bulk-entries`, `cm:stacks:bulk-assets`, `cm:stacks:bulk-taxonomies` |

## Installable

| Package | Commands |
| --- | --- |
| `contentstack-cli-tsgen` | `tsgen` |
| `@contentstack/apps-cli` | `app:create`, `app:get`, `app:update`, `app:delete`, `app:install`, `app:uninstall`, `app:reinstall`, `app:deploy` |
| `@contentstack/cli-launch` | `launch`, `launch:logs`, `launch:functions` |
| `@contentstack/cli-cm-export-query` | query-based export |
| `contentstack-cli-content-type` | inspect content types |
| `@contentstack/cli-cm-regex-validate` | validate regex properties on fields |
| `@contentstack/cli-cm-migrate-rte` | migrate HTML RTE content to JSON RTE |
| `@contentstack/cli-external-migrate` | `migrate:*` commands for migrating from Contentful (see the `migration-companion` skill) |

## Import and export modules

`--module` accepts: `stack`, `assets`, `locales`, `environments`, `extensions`, `webhooks`, `global-fields`, `entries`, `content-types`, `custom-roles`, `workflows`, `publishing-rules`, `labels`, `marketplace-apps`, `taxonomies`, `personalize`, `composable-studio`, plus `variant-entries` on import.
