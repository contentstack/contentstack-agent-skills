---
title: "TypeScript Delivery SDK API Reference"
description: "Reference guide for Contentstack's TypeScript Delivery SDK: Explore features and functions for seamless content delivery in your projects"
url: "https://www.contentstack.com/docs/developers/sdks/content-delivery-sdk/typescript/reference.md"
product: "Contentstack"
doc_type: "guide"
audience:
  - developers
  - admins
version: "current"
last_updated: "2026-02-27"
---

# TypeScript Delivery SDK API Reference

## TypeScript Delivery SDK API Reference

## Overview

Contentstack offers the TypeScript Delivery SDK for building applications. Below, is an in-depth guide and valuable resources to initiate your journey with our TypeScript Delivery SDK. Additionally, the SDK supports the creating applications for Node.js and React Native environments.

**Additional Resource**: To know more about the TypeScript Delivery SDK, refer to the [About TypeScript Delivery SDK](https://www.contentstack.com/docs/developers/sdks/content-delivery-sdk/typescript/about-typescript-delivery-sdk.md) and [Get Started with TypeScript Delivery SDK](https://www.contentstack.com/docs/developers/sdks/content-delivery-sdk/typescript/get-started-with-typescript-delivery-sdk.md) documentation.

## Contentstack

The Contentstack module contains the instance of a stack. To import Contentstack, refer to the code below:

import contentstack from '@contentstack/delivery-sdk';

## Stack

A [stack](https://www.contentstack.com/docs/developers/set-up-stack/about-stack.md) is a repository or a container that holds all the [entries](https://www.contentstack.com/docs/content-managers/author-content/about-entries.md)/[assets](https://www.contentstack.com/docs/content-managers/working-with-assets/about-assets.md) of your site. It allows multiple users to [create](https://www.contentstack.com/docs/content-managers/working-with-entries/create-an-entry.md), [edit](https://www.contentstack.com/docs/content-managers/working-with-entries/edit-an-entry.md), [approve](https://www.contentstack.com/docs/content-managers/use-workflows/send-an-entry-for-publish-or-unpublish-approval.md), and [publish](https://www.contentstack.com/docs/content-managers/publish-content.md) their content within a single space.

The stack function initializes an instance of the Stack. To initialize a stack execute the following code:

import contentstack from '@contentstack/delivery-sdk'  
const stack = contentstack.stack({ apiKey: "apiKey", deliveryToken: "deliveryToken", environment: "environment" });

## LivePreviewConfig

Configuration settings to enable live preview functionality and fetch real-time content data.

Specifies whether to enable the live preview feature.

Specifies the host domain used to retrieve live preview content.

Token required to fetch live preview content from the stack.

## Plugins

When creating custom plugins, through this request, you can pass the details of your custom plugins. This facilitates their utilization in subsequent requests when retrieving details.

To initializing a stack with plugins, refer to the code snippet below:

// custom class for plugin  
class CrossStackPlugin {  
 onRequest (request) {  
 // add request modifications

    return request

}  
 async onResponse (request, response, data) {  
 // add response modifications here

    return response

}  
}  
const Stack = Contentstack.stack({  
 api_key,  
 delivery_token,  
 environment,  
 plugins: \[  
 new CrossStackPlugin(),  
 \]  
});

## Asset

The Asset method by default creates an object for all assets of a stack. To retrieve a single asset, specify its UID.

UID of the asset

## ContentType

The ContentType method retrieves all the content types of a stack. To retrieve a single contenttype, specify its UID.

UID of the content type

## setLocale

The setLocale method sets the locale of the API server.

Enter the locale code

## sync

The sync method syncs your Contentstack data with your app and ensures that the data is always up-to-date by providing delta updates.

An object that supports ‘locale’, ‘start_date’, ‘content_type_uid’, and ‘type’ queries

Specifies if the sync should be recursive

API key of the stack

Delivery token to retrieve data from the stack

Environment name where content is published

The Live preview configuration for the Contentstack API

Name of the branch to fetch data from

Sets the host of the API server  
(example: "dev.contentstack.com")

Region of the stack. You can choose from five regions: NA, EU, Azure NA, Azure EU, GCP NA, and GCP EU.

Lets you specify which language to use as source content if the entry does not exist in the specified language.

Specifies the caching strategy. Accepts a string value from the Policy enum.

Defines where the cache is stored. Accepts localStorage or memoryStorage as string values.

Sets the maximum age (in milliseconds) before the cache expires.

Function to serialize data before storing it in the cache.

Function to deserialize data when retrieving it from the cache.

Set early access headers

Method to enable custom logging in the SDK

Add custom plugins to the SDK

## Asset

In Contentstack, any files (images, videos, PDFs, audio files, and so on) that you upload get stored in your repository for future use. This repository of uploaded files is called [assets](https://www.contentstack.com/docs/content-managers/author-content/about-assets.md).

The Asset method by default creates an object for all assets of a stack. To retrieve a single asset, specify its UID.

**Example:**

import contentstack from '@contentstack/delivery-sdk';

import { BaseAsset } from '@contentstack/delivery-sdk';

const stack = contentstack.stack({ apiKey: "apiKey", deliveryToken: "deliveryToken", environment: "environment" });

interface BlogAsset extends BaseAsset {

    title: string;

    description: string;

    url: string;

    // Add other custom properties as needed

}

async function fetchAssets() {

    try {

       const result = await stack.asset(asset\_uid).fetch<BlogAsset\[\]>();

       console.log('Assets Fetched:', assets);

//Add your statements

    } catch (error) {

        console.error('Error fetching asset:', error);

    }

}

fetchAssets();

## fetch

The fetch method retrieves the asset data of the specified asset.

## includeBranch

The includeBranch method includes the branch details in the response.

## includeDimension

The includeDimension method includes the dimensions (height and width) of the image in the result.

## includeFallback

The includeFallback method retrieves the entry in its fallback language.

## locale

The locale method retrieves the assets published in that locale.

## relativeUrls

The relativeUrls method includes the relative URLs of the asset in the result.

## version

The version method retrieves the specified version of the asset in the result.

Version of the required asset

## includeMetadata

The includeMetadata method includes the metadata for getting metadata content for the entry.

## assetFields

The assetFields method determines the optional asset field groups to include in the response.

**Note:** The assetFields method is supported only in the North America (NA) region.

**Response Behavior:**

- Retrieves only the requested asset metadata, keeping asset payloads smaller.
- Applies to published assets from the asset API. It applies to both single-asset responses and multi-asset responses.
- Does not filter which assets appear in the response or restrict them by file type (MIME).
- Requests optional metadata groups in addition to the core fields on BaseAsset, such as the file MIME type (content_type) and the folder flag (is_dir). It does not replace or modify those fields.

**Note:** On asset objects, content_type represents the file’s MIME type, not a Contentstack CMS content type.

**Supported field groups (values):**

- user_defined_fields: Includes stack-defined custom fields on the asset (author-managed key-value data).
- embedded_metadata: Includes metadata extracted from the file (e.g, EXIF or IPTC).
- ai_generated_metadata: Includes AI-generated data (e.g., tags, descriptions, classifications).
- visual_markups: Includes annotation data (e.g., regions, notes, overlays)

Keys that specify asset field groups to retrieve. Provide them as arguments before .fetch() or .find().

UID of the asset

## Asset Collection

The Asset Collection provides methods for filtering and retrieving assets stored in Contentstack. You can retrieve specific assets by UID, tags, or metadata.

**Example:**

const result = stack.asset().find<BlogAsset>()

.then((assets) => console.log(assets))

.catch((error) => console.error("Error fetching assets:", error));

## addParams

The addParam method adds a query parameter to the query.

Add key-value pairs

## find

The find method retrieves all the assets of the stack.

## includeBranch

The includeBranch method includes the branch details in the result.

## includeCount

The includeCount method retrieves count and data of all the objects in the result.

## includeDimension

The includeDimension method includes the dimensions (height and width) of the image in the result

## includeFallback

The includeFallback method retrieves the entry in its fallback language.

## locale

The locale method retrieves the asset published in the specified locale.

Locale of the asset

## orderByAscending

The orderByAscending method sorts the results in ascending order based on the specified field UID.

Field UID to sort the results

## orderByDescending

The orderByDescending method sorts the results in descending order based on the specified key.

Field UID to sort the results

## param

The param method adds query parameters to the URL.

Add any param to include in the response

Add the corresponding value of the param key

## relativeUrls

The relativeUrls method includes the relative URLs of all the assets in the result.

## removeParam

The removeParam method removes a query parameter from the query.

Specify the param key you want to remove

## version

The version method retrieves a specific version of the asset in the result.

Version number of the asset

## where

The where method filters the results based on the specified criteria.

Specify the field the comparison is made from

Specify the comparison criteria

Specify the field the comparison is made to

## includeMetadata

The includeMetadata method includes the metadata for getting metadata content for the entry.

## skip

The skip method will skip a specific number of assets in the output.

Enter the number of assets to be skipped.

## limit

The limit method will return a specific number of assets in the output.

Enter the maximum number of assets to be returned.

## ContentType

A [content type](https://www.contentstack.com/docs/developers/create-content-types/about-content-types.md) is the structure or blueprint of a page or a section that your web or mobile property will display. It lets you define the overall schema of this blueprint by adding fields and setting its properties.

**Example:**

import { BaseContentType } from '@contentstack/delivery-sdk'

interface BlogPost extends BaseContentType {

text: string;

// other custom props

}

async function fetchContentType() {

try {

const contentType = await stack.contentType("blog").fetch<BlogPost>();

console.log(contentType);

//Add your statements

    } catch (error) {

console.error("Error fetching content type:", error);

}

}

fetchContentType();

## entry

The entry method creates an entry object for the specified entry.

UID of the entry

## fetch

The fetch method retrieves the details for the specified content type.

UID of the content type

## ContentType Collection

The ContentType Collection method retrieves a list of all content types available within a stack. It provides metadata and structural details for each content type but does not retrieve actual content entries.

**Example:**

const contentType = await stack.contentType().find<BlogPost>();

## find

The find method retrieves all the content types of the stack.

## includeGlobalFieldSchema

The includeGlobalFieldSchema method includes the schema of the global field in the response.

## Entry

An [Entry](https://www.contentstack.com/docs/content-managers/author-content/about-entries.md) is the actual piece of content created using one of the defined content types. To work with a single entry, specify its UID.

**Example:**

import contentstack from '@contentstack/delivery-sdk'

import { BaseEntry } from '@contentstack/delivery-sdk'

const stack = contentstack.stack({ apiKey: "apiKey", deliveryToken: "deliveryToken", environment: "environment" });

interface BlogPostEntry extends BaseEntry {

// custom entry types

}

async function fetchEntry() {

    try {

const result = await stack.contentType(contenttype_uid).entry(entry_uid).fetch<BlogPostEntry>();

      console.log('Entry: ', result);

//Add your statements

    } catch (error) {

      console.error('Error fetching entry:', error);

}

}

fetchEntry();

## fetch

The fetch method retrieves the details of a specific entry.

## includeBranch

The includeBranch method includes the branch details in the result.

## includeFallback

The includeFallback method retrieves the entry in its fallback language.

## locale

The locale method retrieves the entries published in that locale.

Locale of the entry

## addParams

The addParam method adds a query parameter to the query.

Add key-value pairs

## except

The except method excludes specific field(s) of an entry.

UID of the field to exclude

## find

The find method retrieves the details of the specified entry.

## skip

The skip method will skip a specific number of entries in the output.

Enter the number of entries to be skipped.

## limit

The limit method will return a specific number of entries in the output.

Enter the maximum number of entries to be returned.

## includeCount

The includeCount method retrieves the count and data of objects in the result.

## only

The only method selects specific field(s) of an entry.

UID of the field to select

## orderByAscending

The orderByAscending sorts the results in ascending order based on the specified field UID.

Field UID to sort the results

## orderByDescending

The orderByDescending sorts the results in descending order based on the specified field UID.

Field UID to sort the results

## param

The param method adds query parameters to the URL.

Add any param to include in the response

Add the corresponding value of the param key

## query

The query method retrieves the details of the entry on the basis of the queries applied.

Query in object format

## removeParam

The removeParam method removes a query parameter from the query.

Specify the param key you want to remove

## where

The where method filters the results based on the specified criteria.

Specify the field the comparison is made from

Specify the comparison criteria

Specify the field the comparison is made to

## includeMetadata

The includeMetadata method includes the metadata for getting metadata content for the entry.

## includeEmbeddedItems

The includeEmbeddedItems method includes embedded objects (Entry and Assets) along with entry details

## includeContentType

The includeContentType method includes the details of the content type along with the Entry details.

## includeReference

The includeReference method retrieves the content of the referred entries in your response.

UID of the reference field to include

## Variants

Variants are different versions of content designed to meet specific needs or target audiences. This feature allows content editors to create multiple variations of a single entry, each customized for a particular variant group or purpose.

When Personalize creates a variant in the CMS, it assigns a "Variant Alias" to identify that specific variant. When fetching entry variants using the Delivery API, you can pass variant aliases in place of variant UIDs in the x-cs-variant-uid header.

## assetFields

The assetFields method specifies the optional asset field groups to include for assets returned with an entry.

**Note:** The assetFields method is supported only in the North America (NA) region.

**Response Behavior:**

- Retrieves only the required asset metadata, keeping the entry payloads smaller when entries reference assets.
- Applies to published assets referenced or embedded on the entry. It applies to both single-entry and multi-entry responses.
- Adds optional metadata fields to each asset in the response. It does not filter assets or control file types.
- Requests optional metadata groups in addition to standard asset fields such as file MIME type (content_type) and folder flag (is_dir). It does not replace or modify core asset fields.

**Note:** On asset objects, content_type represents the file’s MIME type, not a Contentstack CMS content type.

**Supported field groups (values):**

- user_defined_fields: Includes stack-defined custom fields on the asset (author-managed key-value data).
- embedded_metadata: Includes metadata extracted from the file (e.g, EXIF or IPTC).
- ai_generated_metadata: Includes AI-generated data (e.g., tags, descriptions, classifications).
- visual_markups: Includes annotation data (e.g., regions, notes, overlays)

Keys that specify asset field groups to retrieve for assets in the entry response. Provide them as arguments before .fetch() or .find().

UID of the entry

## Query

These methods allow you to refine entry queries by applying conditions, filters, and relational data. You can filter entries based on specific field values, include referenced entries, and limit the number of results.

**Example:**

const query = stack.contentType("contentTypeUid").Entry().query();

## addParams

The addParam method adds a query parameter to the query.

Add key-value pairs

## addQuery

The addQuery method adds multiple query parameters to the query.

Add filter query key

Add the corresponding value to the filter query key

## find

The find method retrieves the details of the specified entry.

## includeCount

The includeCount method retrieves count and data of objects in the result.

## orderByAscending

The orderByAscending method sorts the results in ascending order based on the specified field UID.

Field UID to sort the results

## orderByDescending

The orderByDescending method sorts the results in descending order based on the specified key.

Field UID to sort the results

## param

The param method adds query parameters to the URL.

Add any param to include in the response

Add the corresponding value of the param key

## queryOperator

The queryOperator method retrieves the entries as per the given operator.

Type of query operator to apply

Query instances to apply the query to

## removeParam

The removeParam method removes a query parameter from the query.

Specify the param key you want to remove

## where

The where method filters the results based on the specified criteria.

Specify the field the comparison is made from

Specify the comparison criteria

Specify the field the comparison is made to

## whereIn

The whereIn method retrieves the entries that meet the query conditions made on referenced fields.

UID of the reference field to query

Query instance to include in the where clause

## whereNotIn

The whereNotIn method retrieves the entries that do not meet the query conditions made on referenced fields.

UID of the reference field to query

Query instance to include in the where clause

## skip

The skip method will skip a specific number of entries in the output.

Enter the number of entries to be skipped.

## limit

The limit method will return a specific number of entries in the output.

Enter the maximum number of entries to be returned.

## or

The or method retrieves the entries that meet either of the conditions specified.

Array of query objects or raw queries

## and

The and method retrieves the entries that meet all the specified conditions.

Array of query objects or raw queries

## containedIn

The containedIn method retrieves the entries that contain the conditions specified.

UID of the field

Array of values that are to be used to match or compare

## notContainedIn

The notContainedIn method retrieves the entries where the specified conditions are absent.

UID of the field

Array of values that are to be used to match or compare

## equalTo

The equalTo method retrieves entries that match the specified conditions exactly.

UID of the field

Array of values that are to be used to match or compare

## exists

The exists method retrieves the entries that satisfy the specified condition of existence.

UID of the field

## notExists

The notExists method retrieves entries where the specified conditions are not met.

UID of the field

## getQuery

The getQuery method retrieves the entries as per the specified query.

UID of the field

## greaterThan

The greaterThan method retrieves the entries that are greater than the specified condition.

UID of the field

Array of values that are to be used to match or compare

## greaterThanOrEqualTo

The greaterThanOrEqualTo method retrieves entries that meet the specified condition of being greater than or equal to a certain value.

UID of the field

Array of values that are to be used to match or compare

## lessThan

The lessThan method retrieves the entries that are less than the specified condition.

UID of the field

Array of values that are to be used to match or compare

## lessThanOrEqualTo

The lessThanOrEqualTo method retrieves entries that meet the specified condition of being less than or equal to a certain value.

UID of the field

Array of values that are to be used to match or compare

## referenceIn

The referenceIn method retrieves the entries that are referenced.

UID of the reference field

RAW (JSON) queries

## referenceNotIn

The referenceNotIn method retrieves the entries where the referenced items are not included.

UID of the reference field

RAW (JSON) queries

## regex

The regex method retrieves entries that match a specified regular expression pattern.

UID of the field

Array of values that are to be used to match or compare

Match or compare value in entry

## search

The search method retrieves the entries that match the specified search criteria.

UID of the field

## tags

The tags method fetches the entries that are associated with specific tags.

Array of tags

## Taxonomy

[Taxonomy](https://www.contentstack.com/docs/developers/taxonomy/about-taxonomy.md) helps you categorize pieces of content within your stack to facilitate easy navigation, search, and retrieval of information.

**Note**: All methods in the Query section are applicable for taxonomy-based filtering as well.

## equalAndBelow

The equalAndBelow operation retrieves all entries for a specific taxonomy that match a specific term and all its descendant terms, requiring only the target term.

Enter the UID of the taxonomy

Enter the UID of the term

Enter the level

## below

The below operation retrieves all entries for a specific taxonomy that match all of their descendant terms by specifying only the target term and a specific level.

**Note:** If you don't specify the level, the default behavior is to retrieve terms up to level **10**.

Enter the UID of the taxonomy

Enter the UID of the term

Enter the level

## equalAndAbove

The equalAndAbove operation retrieves all entries for a specific taxonomy that match a specific term and all its ancestor terms, requiring only the target term and a specified level

**Note:** If you don't specify the level, the default behavior is to retrieve terms up to level **10**.

Enter the UID of the taxonomy

Enter the UID of the term

Enter the level

## above

The equalAndAbove operation retrieves all entries for a specific The above operation retrieves all entries for a specific taxonomy that match only the parent terms of a specified target term, excluding the target term itself and a specified level.

**Note:** If you don't specify the level, the default behavior is to retrieve terms up to level **10**.

Enter the UID of the taxonomy

Enter the UID of the term

Enter the level

## fetch

The fetch method retrieves taxonomy data for the specified taxonomy UID.

Specifies the UID of the taxonomy to fetch.

## find

The find method retrieves all published taxonomies in the stack.

- Returns a response object containing:
  - taxonomies: Array of taxonomy objects.
  - count: Optional total number of taxonomies.
- Supports locale and query parameters when configured.

## Terms

Terms serve as the primary classification elements within a taxonomy, allowing you to establish hierarchical structures and incorporate them into entries.

Use the Terms to fetch individual terms, list terms within a taxonomy, and traverse term hierarchies such as ancestors and descendants.

**Note:** The Delivery SDK uses .term() (singular) to access term-level operations, whereas the JavaScript Management SDK uses .terms() (plural) for term-related methods.

**Terms Methods Overview**

Use the following methods to retrieve term data within a taxonomy:

- **fetch**: Retrieves a single term by UID.
- **find**: Retrieves all terms within a specific taxonomy.
- **locales**: Retrieves all available localized versions of a single term.
- **ancestors**: Retrieves all ancestor terms of a single term, up to the root.
- **descendants**: Retrieves all descendant terms of a single term.

import contentstack, { BaseTerm } from '@contentstack/delivery-sdk'

interface BlogPostTerm extends BaseTerm {
// custom term types
}

const stack = contentstack.stack({ apiKey: "apiKey", deliveryToken: "deliveryToken", environment: "environment" });

const data = await stack.taxonomy("taxonomy_uid").term("term_uid").fetch<BlogPostTerm>();

Specifies the term's UID to retrieve.

## fetch

Fetches the details of a single published term within a taxonomy.

Only published terms are returned. This is enforced by the Delivery API and the delivery token used during stack initialization.

If a locale is specified during stack initialization, it is applied automatically to this request.

## find

Fetches a list of all published terms within a specific taxonomy

## locales

Fetches the specified term across all locales configured in the stack.

## ancestors

Fetches all ancestors of a single published term, up to the root.

## descendants

Fetches all descendants of a single published term.

## Global Fields

A [Global field](https://www.contentstack.com/docs/developers/global-field/about-global-field.md) is a reusable field (or group of fields) that you can define once and reuse in any content type within your stack. This eliminates the need (and thereby time and efforts) to create the same set of fields repeatedly in multiple content types.

**Example:**

const globalField = stack.globalField('global_field_uid'); // For a single globalField with uid 'global_field_uid'

## find

The find method retrieves all the global fields of the stack.

## fetch

The fetch method retrieves the global field data of the specified global field.

## includeBranch

The includeBranch method includes the branch details in the result for single or multiple global fields.

UID of the Global field

## Pagination

In a single instance, a query will retrieve only the first 100 items in the response. You can paginate and retrieve the rest of the items in batches using the skip and limit parameters in subsequent requests.

**Example:**

const query = stack.contentType("contentTypeUid").entry().query();  
const pagedResult = await query  
 .paginate()  
 .find<BlogPostEntry>();  
// OR  
const pagedResult = await query  
 .paginate({ skip: 20, limit: 20 })  
 .find<BlogPostEntry>();

## next

The next method retrieves the next set of response values and skips the current number of responses.

## previous

The previous method retrieves the previous set of response values and skips the current number of responses.

## ImageTransform

Image transformations can be performed on images by specifying the desired parameters. The parameters control the specific transformations that will be applied to the image.

**Example:**

const url = 'www.example.com';  
const transformObj = new ImageTransform().bgColor('cccccc');

const transformURL = url.transform(transformObj);

## auto

The auto method enables the functionality that automates certain image optimization features.

## bgColor

The bgColor method sets a background color for the given image.

Color of the background

## blur

The blur method allows you to decrease the focus and clarity of a given image.

Set the blur intensity between 1 to 1000

## brightness

The brightness method enables the functionality that automates certain image optimization features.

Set the brightness of the image between -100 to 100

## canvas

The canvas method allows you to increase the size of the canvas that surrounds an image.

Specifies what params to use for creating canvas - DEFAULT, ASPECTRATIO, REGION, OFFSET

Sets height of the canvas

Sets width of the canvas

Defines the X-axis position of the top left corner or horizontal offset

Defines the Y-axis position of the top left corner or vertical offset

## contrast

The contrast method enables the functionality that automates certain image optimization features.

Set the contrast of the image between -100 to 100

## crop

The crop method allows you to remove pixels from an image by adjusting the height and width in the percentage value or aspect ratio.

Specify the CropBy type using values DEFAULT, ASPECTRATIO, REGION, or OFFSET.

Specify the width to resize the image to.

The value can be in pixels (for example, 400) or in percentage (for example, 0.60 OR '60p')

Specify the height to resize the image to. The value can be in pixels (for example, 400) or in percentage (for example, 0.60 OR '60p')

For the CropBy Region, specify the X-axis position of the top left corner of the crop. For CropBy Offset, specify the horizontal offset of the crop region.

For CropBy Region, specify the Y-axis position of the top left corner of the crop. For CropBy Offset, specify the vertical offset of the crop region.

Ensures that the output image never returns an error due to the specified crop area being out of bounds. The output image is returned as an intersection of the source image and the defined crop area.

Ensures crop is done using content-aware algorithms. Content-aware image cropping returns a cropped image that automatically fits the defined dimensions while intelligently including the most important components of the image.

## dpr

The dpr method lets you deliver images with appropriate size to devices that come with a defined device pixel ratio.

Specify the device pixel ratio. The value should range between 1-10000 or 0.0 to 9999.999

## fit

The fit method enables you to fit the given image properly within the specified height and width.

Specifies fit type (Bounds or Crop)

## format

The format method lets you convert a given image from one format to another.

Specify the format

## frame

The frame method retrieves the first frame from an animated GIF (Graphics Interchange Format) file that comprises a sequence of moving images.

## orient

The orient method allows you to rotate or flip an image in any direction.

Type of Orientation. Values are DEFAULT, FLIP_HORIZONTAL, FLIP_HORIZONTAL_VERTICAL, FLIP_VERTICAL, FLIP_HORIZONTAL_LEFT, RIGHT, FLIP_HORIZONTAL_RIGHT, LEFT.

## overlay

The overlay method lets you place one image over another by specifying the relative URL of the image.

URL of the image to overlay on base image

Lets you define the position of the overlay image. Accepted values are TOP, BOTTOM, LEFT, RIGHT, MIDDLE, CENTER

Lets you define how the overlay image will be repeated on the given image. Accepted values are X, Y, BOTH

Lets you define the width of the overlay image. For pixels, use any whole number between 1 and 8192. For percentages, use any decimal number between 0.0 and 0.99

Lets you define the height of the overlay image. For pixels, use any whole number between 1 and 8192. For percentages, use any decimal number between 0.0 and 0.99

Lets you add extra pixels to the edges of an image. This is useful if you want to add whitespace or border to an image

## padding

The padding method lets you add extra pixels to the edges of an image's border or add whitespace.

padding value in pixels or percentages

## quality

The quality method lets you control the compression level of images that have lossy file format.

Quality range: 1 - 100

## resize

The resize method lets you resize the image in terms of width, height, upscaling the image.

Specifies the width to resize the image to. The value can be in pixels (for example, 400) or in percentage (for example, 0.60 OR '60p')

Specifies the height to resize the image to.The value can be in pixels (for example, 400) or in percentage (for example, 0.60 OR '60p')

The disable parameter disables the functionality that is enabled by default. As of now, there is only one value, i.e., upscale, that you can use with the disable parameter.

## resizeFilter

The resizeFilter method allows you to increase or decrease the number of pixels in a given image.

Types of Filter to apply. Values are NEAREST, BILINEAR, BICUBIC, LANCZOS2, LANCZOS3.

## saturation

The saturation method allows you to increase or decrease the intensity of the colors in a given image.

To set the saturation of image between -100 to 100

## sharpen

The sharpen method allows you to increase the definition of the edges of objects in an image.

Specifies the amount of contrast to be set for the image edges between the range \[0-10\]

Specifies the radius of the image edges between the range \[1-1000\]

Specifies the range of image edges that need to be ignored while sharpening between the range \[0-255\]

## trim

The trim method lets you trim an image from the edges.

Specifies values for top, right, bottom, and left edges of an image.
