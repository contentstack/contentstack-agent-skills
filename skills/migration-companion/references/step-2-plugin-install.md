# Step 2 — Install the migrate CLI plugin (detailed procedure)

> **When to read:** Before running Step 2. Contains the install/update block and how to interpret each result marker. This file is part of the [migration-companion skill](../SKILL.md); `<SKILL_DIR>` refers to that skill's install directory.

The `csdx migrate:*` commands come from `@contentstack/cli-external-migrate`. Run this block to
install or update it automatically — it is intentionally silent unless something changes or fails:

```bash
# Use the Node that Step 1 validated (NODE_BIN_DIR from the prereq check). Omit this line only if
# the check reported no node.bin_dir.
export PATH="<NODE_BIN_DIR>:$PATH"

PLUGIN_NAME="@contentstack/cli-external-migrate"

# Version currently installed (empty string if not installed)
INSTALLED=$(csdx plugins 2>/dev/null \
  | grep -F "$PLUGIN_NAME" \
  | grep -oE '[0-9]+\.[0-9]+\.[0-9]+[^ ]*' \
  | head -1)

# Latest version on npm
LATEST=$(npm view "$PLUGIN_NAME" version 2>/dev/null)

if [ -z "$LATEST" ]; then
  echo "PLUGIN_NPM_UNAVAILABLE"
elif [ -z "$INSTALLED" ]; then
  csdx plugins:install "$PLUGIN_NAME" && echo "PLUGIN_INSTALLED:$LATEST" || echo "PLUGIN_INSTALL_FAILED"
elif [ "$INSTALLED" = "$LATEST" ]; then
  echo "PLUGIN_UP_TO_DATE:$INSTALLED"
else
  csdx plugins:install "$PLUGIN_NAME@$LATEST" \
    && echo "PLUGIN_UPDATED:$INSTALLED→$LATEST" \
    || echo "PLUGIN_UPDATE_FAILED:$INSTALLED→$LATEST"
fi
```

Interpret the last line:

- **`PLUGIN_UP_TO_DATE:<version>`** → already on the latest version; proceed to the Step 2 Eval in [SKILL.md](../SKILL.md). (Stay
  silent — don't report "already up to date" to the user.)
- **`PLUGIN_INSTALLED:<version>`** → freshly installed. Briefly tell the user, then proceed.
- **`PLUGIN_UPDATED:<old>→<new>`** → installed the latest version over the old one. Briefly tell
  the user the plugin was updated, then proceed.
- **`PLUGIN_INSTALL_FAILED`** / **`PLUGIN_UPDATE_FAILED:<old>→<new>`** → the install or
  reinstall errored. Show the user the error output, then display this message and wait:

  > The automatic plugin install failed. Please run the following command manually in your
  > terminal, then click **Continue** when done:
  >
  > ```
  > PATH="<NODE_BIN_DIR>:$PATH" csdx plugins:install @contentstack/cli-external-migrate
  > ```

  Fill in `<NODE_BIN_DIR>` with the recorded value before showing this message.

  After the user clicks Continue, skip straight to the Step 2 **Eval** in [SKILL.md](../SKILL.md)
  to verify the plugin is working before proceeding.

- **`PLUGIN_NPM_UNAVAILABLE`** → `npm view` returned nothing (network issue or package not yet
  published). Show the user this message and wait:

  > Could not reach npm to check the plugin version. Please run the following command manually
  > in your terminal, then click **Continue** when done:
  >
  > ```
  > PATH="<NODE_BIN_DIR>:$PATH" csdx plugins:install @contentstack/cli-external-migrate
  > ```

  Fill in `<NODE_BIN_DIR>` with the recorded value before showing this message.

  After the user clicks Continue, proceed to the Step 2 **Eval** in [SKILL.md](../SKILL.md).

