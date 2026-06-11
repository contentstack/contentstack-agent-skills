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