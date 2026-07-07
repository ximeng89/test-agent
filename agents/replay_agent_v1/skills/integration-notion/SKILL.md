---
name: "integration-notion"
description: "Use the Notion declarative plugin through the plugin gateway."
---

# Notion Plugin Skill

Use the Notion plugin by calling the gateway at `http://workbench:3000/plugins/invoke` with:

- `agentId`: the current agent id
- `pluginKey`: `com.notion`
- `actionKey`: one of the actions listed below
- `connectionKey`: optional, defaults to `default`
- `params`: action input parameters

## Available Actions

1. **getMe**: Verify the current Notion connection and inspect the bound bot user.
2. **listUsers**: List users in the authorized workspace.
3. **search**: Search pages and other searchable content in the workspace.
4. **getPage**: Retrieve one page object by `page_id`.
5. **getBlock**: Retrieve one block object by `block_id`.
6. **listBlockChildren**: List child blocks under a page or block by `block_id`.
7. **getDataSource**: Retrieve one data source object by `data_source_id`.
8. **queryDataSource**: Page through a data source using `start_cursor`.
9. **createPage**: Create a simple child page under a parent page with a title.

## Current Scope And Limits

- This first package version is optimized for Notion OAuth connectivity and read-heavy workflows.
- The current gateway handles scalar template substitution best. That means simple string-based bodies work well, but large nested writes such as rich block trees, filters, and sort arrays should be added later with richer runtime templating support.
- `queryDataSource` currently only exposes cursor-based pagination in a safe way. Complex filters and sorts are intentionally left out of this first package.
- `createPage` is designed for a simple child page with a title. It does not yet create arbitrary block content trees.

## Example Requests

### Example: Search

```json
{
  "agentId": "123",
  "pluginKey": "com.notion",
  "actionKey": "search",
  "connectionKey": "default",
  "params": {
    "query": "roadmap Q3"
  }
}
```

### Example: Get A Page

```json
{
  "agentId": "123",
  "pluginKey": "com.notion",
  "actionKey": "getPage",
  "params": {
    "page_id": "2f8f3e0d-5f7b-4f03-b012-9c0f3b2ce123"
  }
}
```

### Example: List Page Content

```json
{
  "agentId": "123",
  "pluginKey": "com.notion",
  "actionKey": "listBlockChildren",
  "params": {
    "block_id": "2f8f3e0d-5f7b-4f03-b012-9c0f3b2ce123",
    "page_size": 20
  }
}
```

### Example: Create A Child Page

```json
{
  "agentId": "123",
  "pluginKey": "com.notion",
  "actionKey": "createPage",
  "params": {
    "parent_page_id": "2f8f3e0d-5f7b-4f03-b012-9c0f3b2ce123",
    "title": "Daily Sync Notes"
  }
}
```

If the plugin is not authorized yet, ask the user to enable the Notion plugin and complete OAuth before invoking actions.
