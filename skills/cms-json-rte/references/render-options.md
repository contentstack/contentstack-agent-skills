# JSON RTE render recipes

Read this when writing a full `renderOption`, rendering from GraphQL, or rendering JSON RTE as React components. The code targets `@contentstack/utils` 1.9 and `@contentstack/delivery-sdk` 5.x.

## An escaped renderOption

Every function that interpolates content escapes it. URLs pass through `safeUrl`, which only allows `http:`, `https:`, `mailto:` and relative URLs.

```ts
import type { RenderItem, RenderMark, RenderNode, RenderOption } from "@contentstack/utils";

// RenderOption values are a union of function types, so wrap each function to type its parameters.
const node = (fn: RenderNode) => fn;
const mark = (fn: RenderMark) => fn;
const item = (fn: RenderItem) => fn;

const escapeHtml = (value: unknown): string =>
  String(value ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");

const safeUrl = (value: unknown): string => {
  const url = String(value ?? "").trim();
  return /^(https?:|mailto:|\/|#)/i.test(url) ? escapeHtml(url) : "#";
};

export const renderOption: RenderOption = {
  // Node types: `next` renders the children. Leaf text arrives already rendered.
  p: node((n, next) => `<p>${next(n.children)}</p>`),
  h2: node((n, next) => `<h2 class="heading">${next(n.children)}</h2>`),
  a: node(
    (n, next) =>
      `<a href="${safeUrl(n.attrs.url ?? n.attrs.href)}"${
        n.attrs.target === "_blank" ? ' target="_blank" rel="noopener noreferrer"' : ""
      }>${next(n.children)}</a>`
  ),

  // Marks
  bold: mark((text) => `<strong>${text}</strong>`),
  italic: mark((text) => `<em>${text}</em>`),

  // Embedded entries shown as blocks, per content type UID, with a default
  block: {
    product: item(
      (entry) =>
        `<article class="product"><h3>${escapeHtml(entry.title)}</h3><p>${escapeHtml(entry.price)}</p></article>`
    ),
    $default: item((entry) => `<div class="embed">${escapeHtml(entry.title)}</div>`),
  },
  inline: {
    $default: item((entry) => `<span class="embed-inline">${escapeHtml(entry.title)}</span>`),
  },
  // Entries or assets inserted as links
  link: item(
    (entry, metadata) => `<a href="${safeUrl(entry.url)}">${escapeHtml(metadata.text || entry.title)}</a>`
  ),
  // Assets shown as images
  display: item(
    (asset, metadata) =>
      `<img src="${safeUrl(asset.url ?? metadata.attributes["asset-link"])}" alt="${escapeHtml(
        metadata.attributes.alt ?? asset.title ?? ""
      )}" />`
  ),

  // Fallback when an embedded item wasn't returned (not included, or unpublished)
  reference: node(() => ""),
};
```

Keys that aren't in your `renderOption` fall back to the package defaults.

## GraphQL

Query the `json` and the embedded items, with the `system` fields the utils use for matching:

```graphql
query BlogPost($url: String!) {
  all_blog_post(where: { url: $url }) {
    items {
      title
      body {
        json
        embedded_itemsConnection {
          edges {
            node {
              ... on Product {
                title
                price
                system { uid content_type_uid }
              }
              ... on SysAsset {
                title
                url
                system { uid }
              }
            }
          }
        }
      }
    }
  }
}
```

```ts
import { GQL, updateAssetURLForGQL } from "@contentstack/utils";

updateAssetURLForGQL(response);
GQL.jsonToHTML({ entry: response.data.all_blog_post.items, paths: ["body"], renderOption });
// Each item's body is replaced by its HTML string.
```

The GraphQL type name of an embedded content type is generated from its UID (`product` → `Product`). Check the schema if a fragment doesn't match; `cms-graphql` covers the naming rules.

## React components instead of an HTML string

Walk the tree and map node types to elements. Embedded items are looked up from `_embedded_items` (REST and SDK) by UID.

```tsx
import type { ReactNode } from "react";

type RteText = { text: string; bold?: boolean; italic?: boolean; underline?: boolean; inlineCode?: boolean };
type RteNode = { type: string; uid?: string; attrs?: Record<string, any>; children?: Array<RteNode | RteText> };
type Embedded = { uid: string; _content_type_uid?: string; title?: string; url?: string; [key: string]: any };

const isText = (node: RteNode | RteText): node is RteText => "text" in node;

function renderText(leaf: RteText, key: number): ReactNode {
  let out: ReactNode = leaf.text;
  if (leaf.inlineCode) out = <code>{out}</code>;
  if (leaf.bold) out = <strong>{out}</strong>;
  if (leaf.italic) out = <em>{out}</em>;
  if (leaf.underline) out = <u>{out}</u>;
  return <span key={key}>{out}</span>;
}

export function JsonRte({ doc, embedded = [] }: { doc: RteNode; embedded?: Embedded[] }) {
  const byUid = new Map(embedded.map((item) => [item.uid, item]));

  const renderNode = (node: RteNode | RteText, key: number): ReactNode => {
    if (isText(node)) return renderText(node, key);
    const children = node.children?.map(renderNode);
    const attrs = node.attrs ?? {};
    switch (node.type) {
      case "doc":
        return <>{children}</>;
      case "p":
        return <p key={key}>{children}</p>;
      case "h2":
        return <h2 key={key}>{children}</h2>;
      case "ul":
        return <ul key={key}>{children}</ul>;
      case "ol":
        return <ol key={key}>{children}</ol>;
      case "li":
        return <li key={key}>{children}</li>;
      case "a": {
        const href = String(attrs.url ?? attrs.href ?? "");
        return (
          <a key={key} href={/^(https?:|mailto:|\/|#)/i.test(href) ? href : "#"}>
            {children}
          </a>
        );
      }
      case "reference": {
        const item = byUid.get(attrs["entry-uid"] ?? attrs["asset-uid"]);
        if (!item) return null;
        if (attrs.type === "asset") return <img key={key} src={item.url} alt={attrs.alt ?? item.title ?? ""} />;
        return <EmbeddedEntry key={key} entry={item} display={attrs["display-type"]} />;
      }
      default:
        return <div key={key}>{children}</div>;
    }
  };

  return <>{renderNode(doc, 0)}</>;
}

function EmbeddedEntry({ entry, display }: { entry: Embedded; display?: string }) {
  if (display === "inline") return <span>{entry.title}</span>;
  return <aside data-content-type={entry._content_type_uid}>{entry.title}</aside>;
}
```

Pass `embedded={Object.values(entry._embedded_items ?? {}).flat()}`. React escapes text and attribute values, so this path doesn't need `escapeHtml`, but URLs still need the scheme check. Extend the `switch` with the node types your content uses (`h1`–`h6`, `blockquote`, `code`, `table`, `img`, `embed`, `hr`). Before you build a full renderer, check for a maintained community package that fits your framework.
