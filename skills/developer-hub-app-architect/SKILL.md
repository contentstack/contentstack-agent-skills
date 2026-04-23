---
name: developer-hub-app-architect
description: "Turn Contentstack Developer Hub and Marketplace app ideas into concrete implementations. Choose the right UI location, map the architecture, generate boilerplate-aligned React/TypeScript code, and troubleshoot setup, SDK, manifest, proxy, and publishing issues."
allowed-tools: Read Grep Glob
context: fork
agent: plan
---

# Developer Hub App Architect

## Description

Turn Contentstack Developer Hub and Marketplace app ideas into concrete implementations. Choose the right UI location, map the architecture, generate boilerplate-aligned React/TypeScript code, and troubleshoot setup, SDK, manifest, proxy, and publishing issues.

## When to Use

Use when a user needs help designing or building a Contentstack Developer Hub or Marketplace app.
Use when choosing the right UI location for a feature.
Use when generating app code from the marketplace boilerplate or a similar starter.
Use when explaining manifest, setup, proxy, OAuth, or publishing steps.
Use when debugging app loading, SDK, iframe, route, or location issues.

## User Problem

Users need to turn app ideas into working Contentstack apps without guessing at UI locations, Developer Hub setup, or SDK integration details. They also need help debugging broken app assumptions quickly and consistently.

## Success Criteria

Selects the best UI location(s) with clear tradeoffs when multiple options fit.
Produces implementation-ready React/TypeScript guidance aligned to the user’s boilerplate.
Includes the necessary Developer Hub, manifest, route, proxy, and install steps.
Avoids exposing secrets and keeps credentials server-side.
Uses a repeatable troubleshooting checklist for broken apps.

## Expected Inputs

- App idea or feature description
- Target Contentstack UI location or candidate locations
- Boilerplate structure or repo conventions
- Manifest or route details
- Proxy, config, or OAuth requirements
- Error messages, screenshots, or runtime symptoms for debugging

## Expected Outputs

- Recommended UI location(s) and rationale
- Architecture and route map
- Manifest and Developer Hub setup checklist
- Code scaffold or concrete code changes
- Config schema and proxy guidance
- Test, install, and deployment checklist
- Troubleshooting diagnosis and next steps

## Example User Requests

- Build a private Contentstack app that adds AI suggestions in the entry sidebar.
- Which UI location should I use for a product taxonomy picker?
- Generate an app configuration page and save API credentials through proxy variables.
- Create a marketplace-ready app from our boilerplate with dashboard + custom field routes.
- Why is my app loading but appSdk.location.CustomField is undefined?
- Turn this app idea into manifest config, route plan, and starter code.

## Workflow Summary

Understand the app idea, constraints, and required integrations.
Choose the best UI location(s) and explain tradeoffs.
Map the app architecture to the boilerplate and route structure.
Generate code, config, and Developer Hub setup steps.
Add test, install, and publishing checks.
Debug issues using route, manifest, location, SDK, config, and proxy assumptions.

## Instructions

### Operating modes

Switch between advisor mode and builder mode. In advisor mode, choose the best UI location(s), explain tradeoffs, review architecture, and debug issues. In builder mode, generate implementation-ready React/TypeScript code, config, and setup steps aligned to the user’s boilerplate and reference guidance.

### Reference-first implementation

Use the provided references before inventing new patterns. Prefer the user’s boilerplate structure and the Developer Hub guide for location mapping, SDK usage, setup, troubleshooting, and publishing details. If repo details are missing, state the assumed structure explicitly and keep the scaffold minimal.

### Location selection

Always identify the best Contentstack UI location before writing code. Prefer the smallest location that fits the use case. If multiple locations fit, compare them by user context, available SDK surface, and implementation complexity, then recommend one. Consult the location-selection reference before answering.

### Code generation

Generate production-ready React + TypeScript code when asked. Include loading states, error states, typed helpers, and iframe resize behavior by default. Use concrete edits or complete files, not pseudo-code, unless the user asks for a high-level plan. Align code to the boilerplate reference instead of inventing a new structure.

### Developer Hub setup

Include manifest, base URL, route mapping, location enabling, advanced settings variables, proxy/rewrite, install, and deploy steps whenever they affect the implementation. Explain how the app is wired in Developer Hub and what must be configured before testing. Use the Developer Hub setup reference for exact steps.

### SDK and integration patterns

Use @contentstack/app-sdk patterns for location access, config read/write, field updates, asset replacement, iframe sizing, and typed guards. Prefer proxy/API rewrite patterns for external integrations and keep secrets server-side. Consult the SDK patterns reference for canonical usage.

### Troubleshooting

Debug by checking route, manifest, location, SDK init, iframe context, config persistence, proxy behavior, and install scope assumptions in that order. Lead with the most likely cause and the fastest verification step. Use the troubleshooting reference to confirm likely failure modes.

### Publishing and safety

For marketplace or publishing questions, include readiness checks for scopes, permissions, credentials, versioning, and install flow. Never expose OAuth client secrets or app signing keys. Validate scopes and avoid broader permissions than required. Use the marketplace publishing reference when relevant.

## Output Format

Be concise and actionable.
Use bullets for recommendations and checklists.
When code is requested, provide production-ready code or concrete edits, not pseudo-code.
When a decision is unclear, explain the tradeoff and make a recommendation.
When debugging, lead with the most likely cause and the fastest verification step.

## Tooling Notes

Primary tools: Developer Hub API, Apps, Installations, OAuth, UI Locations, App Hosting, Marketplace.
Use Developer Hub Proxy and OAuth Provider when integrations require secure server-side handling.
Prefer marketplace and app-hosting guidance only when relevant to publishing or deployment.
Consult reference files for location selection, boilerplate conventions, SDK patterns, setup, troubleshooting, and publishing notes.

## Security

### Defaults

- Never expose OAuth client secrets or app signing keys.
- Validate all app installation scopes.
- Never grant broader permissions than required.
- Keep app credentials server-side only.

### Destructive Actions

Do not perform destructive actions unless the user explicitly requests them and confirms the target app, environment, or installation. For publish, delete, revoke, or uninstall flows, explain the impact first and require confirmation.

### Secrets

Never reveal, print, or embed secrets in frontend code, examples, logs, or config output. Recommend server-side storage, proxy variables, or secure environment variables for credentials.

### Environment Variables

Use environment variables for server-side configuration only. Do not place secrets in client-visible settings. Document required variables clearly and distinguish public config from private credentials.

## Product Context

- - Product: Developer Hub
- - Description: Contentstack Developer Hub: marketplace apps, custom app development, OAuth app registration, app installations, hosting, UI locations, and the Developer Hub API.
- - Product safety rules: - Never expose OAuth client secrets or app signing keys.
- Validate all app installation scopes.
- Never grant broader permissions than required.
- Keep app credentials server-side only.
- - Default tools: ["Developer Hub API", "Apps", "Installations", "OAuth", "UI Locations", "App Hosting", "Marketplace"]
- - Default connectors: ["Developer Hub Proxy", "OAuth Provider", "Marketplace"]

## References

### Developer Hub coding reference (playbook, required)
- Summary: Contentstack Developer Hub & Custom Apps Guide

# Contentstack Developer Hub & Custom Apps Guide

Complete guide for building custom apps and extensions for Contentstack Developer Hub. This guide covers the App SDK, UI locations, implementation patterns, and best practices for AI coding assistants.

## What is Contentstack Developer Hub?

[Contentstack Developer Hub](https://www.contentstack.com/docs/developers/developer-hub) is a platform that allows developers to build custom applications that extend and enhance the Contentstack CMS experience. It provides APIs, SDKs, and tools to create apps that integrate seamlessly into Contentstack's user interface.

### Key Features

- **App Framework**: Complete framework for building custom apps with React, TypeScript, and modern tooling
- **UI Locations**: Multiple integration points within Contentstack's interface (sidebars, dashboards, custom fields, etc.)
- **SDK Integration**: JavaScript SDK (`@contentstack/app-sdk`) for interacting with Contentstack's APIs and UI
- **Marketplace**: Ability to publish apps to Contentstack's marketplace or keep them private
- **OAuth Integration**: Secure authentication and authorization for apps
- **App Hosting**: Options for external hosting or Contentstack-managed hosting

### Types of Apps

1. **Marketplace Apps**: Public apps available to all Contentstack users
2. **Private Apps**: Organization-specific apps for internal use
3. **Machine-to-Machine Apps**: Apps that interact with Contentstack APIs without user interface

---

## Key Concepts

### App Manifest

The app manifest is configured in the Contentstack Developer Hub platform (not in the codebase). It defines:

- App metadata (name, description, icon)
- UI locations where the app appears
- Routing configuration (paths to your app's routes)
- Hosting information (base URL)
- Visibility settings (public/private)

The manifest configuration is done through the Developer Hub UI when creating or managing your app.

### UI Locations

UI locations are specific places in Contentstack's interface where your app can appear:

| Location           | Path                 | Use Case             | Description                                              |
| ------------------ | -------------------- | -------------------- | -------------------------------------------------------- |
| **Asset Sidebar**  | `/asset-sidebar`     | Actions on assets    | Sidebar in the Asset Library when viewing/editing assets |
| **Entry Sidebar**  | `/entry-sidebar`     | Actions on entries   | Sidebar when editing content entries                     |
| **Custom Field**   | `/custom-field`      | Custom input fields  | Custom field type for content types                      |
| **Dashboard**      | `/stack-dashboard`   | Dashboard widgets    | Widget on the stack dashboard                            |
| **App Config**     | `/app-configuration` | App settings         | Configuration page for app settings                      |
| **Full Page**      | `/full-page`         | Standalone pages     | Standalone full-page app                                 |
| **Field Modifier** | `/field-modifier`    | Modify field values  | Modifies field values programmatically                   |
| **RTE Location**   | `/json-rte.js`       | Rich text extensions | Rich text editor extensions                              |

### App SDK

The `@contentstack/app-sdk` provides:

- **SDK Initialization**: `ContentstackAppSDK.init()` - Initializes the SDK and establishes connection
- **Location Access**: Access to current UI location and its data
- **Asset Operations**: Methods to read, upload, and replace assets
- **Entry Operations**: Methods to read and modify content entries
- **Configuration**: Access to app configuration settings
- **Frame Management**: Control iframe dimensions and auto-resizing
- **API Proxy**: Make external API calls through Contentstack's secure proxy

**Basic SDK Usage:**

```typescript
import ContentstackAppSDK from "@contentstack/app-sdk";

// Initialize SDK
const appSdk = await ContentstackAppSDK.init();

// Access current location
const location = appSdk.location;

// Access configuration
const config = await appSdk.getConfig();

// Access stack data
const stack = appSdk.stack;
```

---

## Architecture Overview

### How Apps Work

Developer Hub apps run in an **iframe** within Contentstack's interface. The app is a standalone React application that communicates with Contentstack via the App SDK.

### Initialization Flow

1. **App Loads**: React app loads in Contentstack's iframe
2. **SDK Initialization**: App calls `ContentstackAppSDK.init()`
3. **Token Validation**: App verifies authentication token from URL
4. **Location Detection**: SDK identifies which UI location is active
5. **Context Setup**: SDK instance and config are provided via React Context
6. **Component Rendering**: UI components access SDK via hooks

### Data Flow

```
Contentstack UI (iframe)
    ↓
MarketplaceAppProvider
    ↓
ContentstackAppSDK.init()
    ↓
React Context (appSdk, appConfig)
    ↓
Location Component (AssetSidebar, EntrySidebar, etc.)
    ↓
useAppSdk() hook
    ↓
Location-specific operations (getData, setData, etc.)
```

---

## Prerequisites

- React and TypeScript knowledge
- Contentstack account with Developer Hub access
- Node.js v18+
- Understanding of iframe communication patterns

---

## Quick Start

### Use the Official Boilerplate (Recommended)

The [Contentstack Marketplace App Boilerplate](https://github.com/contentstack/marketplace-app-boilerplate) provides:

- **Pre-configured SDK Setup**: Ready-to-use `MarketplaceAppProvider` for SDK initialization
- **Custom Hooks**: Pre-built hooks like `useAppSdk`, `useAppLocation`, `useAppConfig`
- **Routing Structure**: React Router setup with lazy loading for optimal performance
- **UI Location Templates**: Scaffolding for all available UI locations
- **Testing Infrastructure**: E2E testing setup with Playwright
- **Build Configuration**: Vite configuration optimized for Contentstack apps
- **TypeScript Support**: Full TypeScript setup with proper type definitions

```bash
# Clone the official boilerplate
git clone https://github.com/contentstack/marketplace-app-boilerplate
cd marketplace-app-boilerplate
npm install
npm run dev
```

### Project Structure

```
src/
├── containers/
│   ├── App/                    # Main app component with routing
│   ├── AssetSidebarWidget/     # Asset sidebar location
│   ├── EntrySidebar/           # Entry sidebar location
│   ├── CustomField/            # Custom field location
│   ├── Dashboard/              # Dashboard widget location
│   └── AppConfiguration/       # App configuration page
├── common/
│   ├── providers/              # React context providers
│   │   └── MarketplaceAppProvider.tsx  # SDK initialization
│   ├── hooks/                   # Custom React hooks
│   │   ├── useAppSdk.tsx       # Access to SDK instance
│   │   └── useAppLocation.ts    # Current UI location
│   └── contexts/                # React contexts
│       └── marketplaceContext.ts
└── components/                  # Reusable components
    └── ErrorBoundary.tsx
```

---

## SDK Initialization

### Provider Setup

The SDK must be initialized once at the app root level:

```typescript
// providers/MarketplaceAppProvider.tsx
import { useEffect, useState } from "react";
import ContentstackAppSDK from "@contentstack/app-sdk";

export function MarketplaceAppProvider({ children }) {
  const [appSdk, setAppSdk] = useState(null);
  const [config, setConfig] = useState(null);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    ContentstackAppSDK.init()
      .then(async (sdk) => {
        setAppSdk(sdk);
        const appConfig = await sdk.getConfig();
        setConfig(appConfig);
      })
      .catch(() => {
        setFailed(true);
      });
  }, []);

  if (failed) return <div>Failed to initialize SDK</div>;
  if (!appSdk) return <div>Loading...</div>;

  return (
    <MarketplaceContext.Provider value={{ appSdk, config }}>
      {children}
    </MarketplaceContext.Provider>
  );
}
```

### Using the SDK Hook

```typescript
// hooks/useAppSdk.tsx
import { useContext } from "react";
import { MarketplaceContext } from "../contexts/marketplaceContext";

export function useAppSdk() {
  const { appSdk } = useContext(MarketplaceContext);
  if (!appSdk) {
    throw new Error("useAppSdk must be used within MarketplaceAppProvider");
  }
  return appSdk;
}
```

### App Root Setup

```typescript
// App.tsx
import { MarketplaceAppProvider } from "./providers/MarketplaceAppProvider";
import { BrowserRouter } from "react-router-dom";

function App() {
  return (
    <MarketplaceAppProvider>
      <BrowserRouter>{/* Your routes */}</BrowserRouter>
    </MarketplaceAppProvider>
  );
}
```

---

## UI Location Implementations

### Asset Sidebar Widget

The Asset Sidebar appears when viewing or editing an asset in Contentstack's Asset Library.

```typescript
// containers/AssetSidebarWidget/AssetSidebar.tsx
import { useState, useEffect } from "react";
import { useAppSdk } from "@/common/hooks/useAppSdk";

export function AssetSidebar() {
  const appSdk = useAppSdk();
  const [asset, setAsset] = useState(null);
  const [loading, setLoading] = useState(true);

  // Get asset sidebar location
  const assetSidebar = (appSdk?.location as any)?.AssetSidebarWidget;

  useEffect(() => {
    if (assetSidebar) {
      // Get current asset data
      assetSidebar.getData().then((data) => {
        setAsset(data);
        setLoading(false);
      });
    }
  }, [assetSidebar]);

  // Replace asset with new file
  const replaceAsset = async (file: File) => {
    try {
      await assetSidebar.replaceAsset(file);
      // Refresh asset data
      const updated = await assetSidebar.getData();
      setAsset(updated);
    } catch (error) {
      console.error("Failed to replace asset:", error);
    }
  };

  if (loading) return <div>Loading asset...</div>;

  return (
    <div>
      <h2>Asset: {asset?.title}</h2>
      <p>Type: {asset?.content_type}</p>
      <p>Size: {asset?.file_size} bytes</p>
      {/* Your custom UI */}
    </div>
  );
}
```

**Available Methods:**

- `getData()` - Get current asset data
- `replaceAsset(file)` - Replace asset with new file
- `onAssetChange(callback)` - Listen for asset changes

### Entry Sidebar Widget

The Entry Sidebar appears when editing a content entry.

```typescript
// containers/EntrySidebar/EntrySidebar.tsx
import { useState, useEffect } from "react";
import { useAppSdk } from "@/common/hooks/useAppSdk";

export function EntrySidebar() {
  const appSdk = useAppSdk();
  const [entry, setEntry] = useState(null);

  const sidebar = appSdk?.location?.SidebarWidget;

  useEffect(() => {
    if (sidebar) {
      // Get entry data
      sidebar.getData().then(setEntry);

      // Listen for save events
      sidebar.onSave(() => {
        console.log("Entry saved");
        // Refresh entry data
        sidebar.getData().then(setEntry);
      });

      // Listen for publish events
      sidebar.onPublish(() => {
        console.log("Entry published");
      });
    }
  }, [sidebar]);

  // Update field value
  const setFieldValue = async (field: string, value: any) => {
    try {
      await sidebar.entry.setField(field, value);
      // Refresh entry data
      const updated = await sidebar.getData();
      setEntry(updated);
    } catch (error) {
      console.error("Failed to set field:", error);
    }
  };

  if (!entry) return <div>Loading entry...</div>;

  return (
    <div>
      <h2>Entry: {entry?.title}</h2>
      <p>Content Type: {entry?.content_type_uid}</p>
      {/* Your custom UI */}
    </div>
  );
}
```

**Available Methods:**

- `getData()` - Get current entry data
- `entry.setField(field, value)` - Update field value
- `entry.getField(field)` - Get field value
- `onSave(callback)` - Listen for save events
- `onPublish(callback)` - Listen for publish events

### Custom Field

Custom fields allow you to create custom input types for content types.

```typescript
// containers/CustomField/CustomField.tsx
import { useState, useEffect } from "react";
import { useAppSdk } from "@/common/hooks/useAppSdk";

export function CustomField() {
  const appSdk = useAppSdk();
  const [value, setValue] = useState("");
  const [fieldConfig, setFieldConfig] = useState(null);

  const customField = appSdk?.location?.CustomField;

  useEffect(() => {
    if (customField) {
      // Get initial value
      customField.field.getData().then(setValue);

      // Get field configuration
      customField.field.getConfig().then(setFieldConfig);
    }
  }, [customField]);

  const handleChange = async (newValue: string) => {
    setValue(newValue);
    // Update field value
    await customField.field.setData(newValue);
  };

  return (
    <div>
      <label>{fieldConfig?.label || "Custom Field"}</label>
      <input
        type="text"
        value={value}
        onChange={(e) => handleChange(e.target.value)}
        placeholder={fieldConfig?.placeholder}
      />
    </div>
  );
}
```

**Available Methods:**

- `field.getData()` - Get current field value
- `field.setData(value)` - Set field value
- `field.getConfig()` - Get field configuration
- `field.setFocus()` - Focus the field

### Dashboard Widget

Dashboard widgets appear on the stack dashboard.

```typescript
// containers/Dashboard/Dashboard.tsx
import { useEffect, useState } from "react";
import { useAppSdk } from "@/common/hooks/useAppSdk";

export function Dashboard() {
  const appSdk = useAppSdk();
  const [stackInfo, setStackInfo] = useState(null);

  useEffect(() => {
    if (appSdk) {
      const stack = appSdk.stack;
      setStackInfo({
        apiKey: stack.getApiKey(),
        name: stack.getName(),
        // ... other stack info
      });
    }
  }, [appSdk]);

  return (
    <div>
      <h2>Stack: {stackInfo?.name}</h2>
      <p>API Key: {stackInfo?.apiKey}</p>
      {/* Your dashboard widget UI */}
    </div>
  );
}
```

### App Configuration Page

The App Configuration page allows users to configure app settings.

```typescript
// containers/AppConfiguration/AppConfiguration.tsx
import { useState, useEffect } from "react";
import { useAppSdk } from "@/common/hooks/useAppSdk";

export function AppConfiguration() {
  const appSdk = useAppSdk();
  const [config, setConfig] = useState({ apiKey: "", enabled: false });
  const [saving, setSaving] = useState(false);

  const appConfig = appSdk?.location?.AppConfigWidget;

  useEffect(() => {
    if (appConfig) {
      // Load existing config
      appConfig.getConfig().then(setConfig);
    }
  }, [appConfig]);

  const saveConfig = async () => {
    setSaving(true);
    try {
      await appConfig.setConfig(config);
      // Show success message
    } catch (error) {
      console.error("Failed to save config:", error);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div>
      <h2>App Configuration</h2>
      <label>
        API Key:
        <input
          value={config.apiKey}
          onChange={(e) => setConfig({ ...config, apiKey: e.target.value })}
          type="password"
        />
      </label>
      <label>
        <input
          type="checkbox"
          checked={config.enabled}
          onChange={(e) => setConfig({ ...config, enabled: e.target.checked })}
        />
        Enable Feature
      </label>
      <button onClick={saveConfig} disabled={saving}>
        {saving ? "Saving..." : "Save"}
      </button>
    </div>
  );
}
```

**Available Methods:**

- `getConfig()` - Get app configuration
- `setConfig(config)` - Save app configuration

---

## API Proxy

Use `appSdk.api()` to make external API calls through Contentstack's secure proxy. This allows you to:

- Keep API keys secure (stored in Developer Hub Advanced Settings)
- Avoid CORS issues
- Use variable substitution for credentials

### Basic Usage

```typescript
// Make API request through Contentstack proxy
const response = await appSdk.api("/external-api/endpoint", {
  method: "POST",
  headers: {
    "x-api-key": "{{var.API_KEY}}", // Variable substitution
    "Content-Type": "application/json",
  },
  body: JSON.stringify(data),
});

const data = await response.json();
```

### Variable Substitution

Variables are configured in Developer Hub Advanced Settings and automatically substituted:

```typescript
// In your code
headers: {
  "x-api-key": "{{var.API_KEY}}",
  "authorization": "Bearer {{var.ACCESS_TOKEN}}",
}

// Contentstack replaces with actual values from Advanced Settings
```

### API Rewrites

Configure URL rewrites in Developer Hub Advanced Settings:

- **Pattern**: `/external-api/*`
- **Target**: `https://api.example.com/*`

This allows you to use relative paths in your code while Contentstack proxies to the actual API.

### Complete Example

```typescript
async function callExternalAPI(prompt: string) {
  const appSdk = useAppSdk();

  try {
    const response = await appSdk.api(
      "/genai/gemini-2.5-flash-image:generateContent",
      {
        method: "POST",
        headers: {
          "x-goog-api-key": "{{var.GEMINI_API_KEY}}",
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          contents: [
            {
              parts: [
                { text: prompt },
                { inline_data: { mime_type: "image/jpeg", data: base64Image } },
              ],
            },
          ],
        }),
      }
    );

    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error("API call failed:", error);
    throw error;
  }
}
```

---

## Frame Management

Control the iframe dimensions to ensure your app displays correctly:

```typescript
const appSdk = useAppSdk();

// Auto-resize iframe based on content
appSdk.location.frame?.autoResizeFrame();

// Set specific height
appSdk.location.frame?.setFrameHeight(400);

// Enable auto-resize with options
appSdk.location.frame?.enableAutoResizing({
  height: true,
  width: false,
});
```

**Best Practice**: Use `autoResizeFrame()` for dynamic content that changes height.

---

## Accessing Configuration

### Get App Configuration

```typescript
const appSdk = useAppSdk();

// Get configuration (set in App Configuration location)
const config = await appSdk.getConfig();
console.log(config.apiKey);
console.log(config.enabled);
```

### Get Stack Information

```typescript
const appSdk = useAppSdk();
const stack = appSdk.stack;

console.log(stack.getApiKey());
console.log(stack.getName());
console.log(stack.getUid());
```

---

## Development Workflow

### 1. Local Development Setup

```bash
# Clone boilerplate
git clone https://github.com/contentstack/marketplace-app-boilerplate
cd marketplace-app-boilerplate

# Install dependencies
npm install

# Start dev server
npm run dev
```

Runs on `http://localhost:3000`

### 2. Configure in Developer Hub

1. **Create App**:

   - Go to Contentstack Developer Hub
   - Click "Create App"
   - Fill in app details (name, description, icon)

2. **Set Base URL**:

   - Set base URL to `http://localhost:3000` (for development)
   - Or use tunneling service (ngrok, Cloudflare Tunnel) for HTTPS

3. **Configure UI Locations**:

   - Add UI locations you want to support
   - Set route paths (e.g., `/asset-sidebar`)

4. **Configure Advanced Settings** (if needed):
   - **API Rewrites**: Add rewrite rules for external APIs
   - **Variables**: Add variables for API keys (accessed via `{{var.NAME}}`)

### 3. Install and Test

1. **Install App**:

   - Go to your test stack
   - Navigate to Apps
   - Install your app

2. **Test Locations**:
   - Open Asset Library → View asset → Check sidebar
   - Edit entry → Check sidebar
   - Go to Dashboard → Check widget
   - Configure app settings → Check config page

### 4. Building for Production

```bash
npm run build
```

Outputs to `dist/` directory.

### 5. Deploy

1. Deploy `dist/` folder to hosting provider (Vercel, Netlify, AWS, etc.)
2. Update app configuration in Developer Hub with production URL
3. Update manifest settings if needed

---

## Error Handling

Always handle errors gracefully:

```typescript
try {
  const data = await assetSidebar.getData();
  setAsset(data);
} catch (error) {
  console.error("Failed to get asset:", error);
  // Show user-friendly error message
  setError("Unable to load asset. Please try again.");
}
```

### Common Error Scenarios

- **SDK not initialized**: Ensure `MarketplaceAppProvider` wraps your app
- **Location not available**: Check if location is configured in Developer Hub
- **API call failed**: Verify API rewrites and variables are configured
- **Permission denied**: Check app permissions in Developer Hub

---

## Best Practices

| Do                               | Don't                              |
| -------------------------------- | ---------------------------------- |
| Initialize SDK once at root      | Re-initialize on every render      |
| Handle loading states            | Show blank screens                 |
| Handle errors gracefully         | Let errors crash app               |
| Use TypeScript                   | Skip type safety                   |
| Test in Contentstack iframe      | Only test standalone               |
| Use config for secrets           | Hardcode API keys                  |
| Use API proxy for external calls | Make direct API calls from browser |
| Auto-resize iframe               | Use fixed heights                  |
| Validate user input              | Trust all input                    |
| Provide user feedback            | Silent failures                    |

---

## Testing

### Unit Tests

```typescript
// __tests__/AssetSidebar.test.tsx
import { render, screen } from "@testing-library/react";
import { AssetSidebar } from "../AssetSidebar";

// Mock SDK
jest.mock("@/common/hooks/useAppSdk", () => ({
  useAppSdk: () => ({
    location: {
      AssetSidebarWidget: {
        getData: jest.fn().mockResolvedValue({ title: "Test Asset" }),
      },
    },
  }),
}));

test("renders asset title", async () => {
  render(<AssetSidebar />);
  expect(await screen.findByText("Test Asset")).toBeInTheDocument();
});
```

### E2E Tests (Playwright)

```typescript
// e2e/asset-sidebar.spec.ts
import { test, expect } from "@playwright/test";

test("asset sidebar loads", async ({ page }) => {
  await page.goto("http://localhost:3000/asset-sidebar");
  await expect(page.locator("h2")).toContainText("Asset:");
});
```

---

## Troubleshooting

### App Not Loading

1. Check browser console for errors
2. Verify base URL is correct in Developer Hub
3. Check if app is installed on the stack
4. Verify HTTPS if using production URL

### SDK Not Initializing

1. Check if `MarketplaceAppProvider` wraps your app
2. Verify authentication token in URL
3. Check browser console for SDK errors
4. Ensure app is properly installed

### Location Not Available

1. Verify location is configured in Developer Hub manifest
2. Check route path matches configuration
3. Ensure location is enabled for the app

### API Calls Failing

1. Verify API rewrites are configured in Advanced Settings
2. Check variables are set correctly (`{{var.NAME}}`)
3. Verify rewrite patterns match your API paths
4. Check network tab for actual request URLs

---

## Resources

- [Contentstack Developer Hub Documentation](https://www.contentstack.com/docs/developers/developer-hub)
- [Contentstack App SDK Reference](https://www.contentstack.com/docs/developers/developer-hub/contentstack-app-development)
- [UI Locations Reference](https://www.contentstack.com/docs/developers/developer-hub/managing-ui-locations)
- [Marketplace App Boilerplate (GitHub)](https://github.com/contentstack/marketplace-app-boilerplate)
- [Marketplace App Boilerplate Documentation](https://www.contentstack.com/docs/developers/developer-hub/marketplace-app-boilerplate)

## Examples

### Choose the right UI location for an AI sidebar feature (few shot *)

**User:** Build a private Contentstack app that adds AI suggestions in the entry sidebar.

**Assistant:** Recommend the Entry Sidebar location because the feature acts on a single entry while editing. If the suggestions need to persist as field values, compare Entry Sidebar vs Custom Field and recommend Entry Sidebar unless the interaction must live inside the field itself. Then outline the route map, SDK data access, manifest locations, and a minimal React/TypeScript scaffold aligned to the boilerplate.

*Advisor mode example: location selection first, then architecture.*

### Generate a config page with proxy-backed credentials (few shot *)

**User:** Generate an app configuration page and save API credentials through proxy variables.

**Assistant:** Build an App Configuration screen with loading, error, and save states. Store credentials server-side through Developer Hub advanced settings variables and API rewrites, not in frontend state or client-visible config. Include the route, config schema, proxy call pattern, and the Developer Hub setup steps needed before testing.

*Builder mode example: implementation-ready output with security constraints.*

### Debug a missing custom field SDK location (few shot *)

**User:** Why is my app loading but appSdk.location.CustomField is undefined?

**Assistant:** Check the configured UI location first: confirm the app is installed with Custom Field enabled and that the route matches the Developer Hub location path. Then verify SDK initialization, inspect the actual location object name used by the boilerplate, and confirm the app is loading inside the Contentstack iframe rather than standalone. If the location name differs in the repo, align the code to the boilerplate conventions and re-test.

*Troubleshooting example: lead with the most likely cause and fastest verification step.*