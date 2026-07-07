---
name: "integration-anthropic"
description: "Use the Anthropic declarative plugin through the plugin gateway."
---

# Anthropic Plugin Skill

Use the Anthropic plugin by calling the gateway at `http://bascilclaw_admin:3000/plugins/invoke` with:

- `agentId`: the current agent id
- `pluginKey`: `com.anthropic`
- `actionKey`: one of the actions listed below
- `connectionKey`: optional, defaults to `default`
- `params`: action input parameters

## Available Actions

1. **getModels**: List Claude models available to the connected API key.
2. **createMessage**: Send a prompt to the Messages API and receive a Claude response.
3. **countTokens**: Estimate token usage for a message payload before sending it.

## Authentication

- This plugin uses `auth.type = api_key`.
- The user should enable the plugin and paste an Anthropic API key when prompted.
- The runtime injects the saved key as `x-api-key`.

## Usage Notes

- `createMessage` currently accepts a single user prompt string plus an optional `system` prompt.
- Pass the target model explicitly, for example `claude-sonnet-4-20250514`.
- Static headers required by Anthropic such as `anthropic-version: 2023-06-01` are already defined in the manifest.

## Examples

### Example: Listing Models

```json
{
  "agentId": "123",
  "pluginKey": "com.anthropic",
  "actionKey": "getModels",
  "connectionKey": "default",
  "params": {}
}
```

### Example: Creating a Message

```json
{
  "agentId": "123",
  "pluginKey": "com.anthropic",
  "actionKey": "createMessage",
  "connectionKey": "default",
  "params": {
    "model": "claude-sonnet-4-20250514",
    "max_tokens": 512,
    "system": "You are a concise assistant.",
    "userPrompt": "Summarize the main idea of the attached design."
  }
}
```

### Example: Counting Tokens

```json
{
  "agentId": "123",
  "pluginKey": "com.anthropic",
  "actionKey": "countTokens",
  "params": {
    "model": "claude-sonnet-4-20250514",
    "userPrompt": "Draft a release note for today's build."
  }
}
```

If the plugin is not authorized yet, ask the user to enable the Anthropic plugin and fill in the API key before invoking actions.
