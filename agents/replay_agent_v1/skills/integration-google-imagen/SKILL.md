---
name: "integration-google-imagen"
description: "Use the Google Imagen declarative plugin through the plugin gateway to generate images."
---

# Google Imagen Plugin Skill

Use the Google Imagen plugin by calling the gateway at `http://bascilclaw_admin:3000/plugins/invoke` with:

- `agentId`: the current agent id
- `pluginKey`: `com.google.imagen`
- `actionKey`: one of the actions listed below
- `connectionKey`: optional, defaults to `default`
- `params`: action input parameters

## Available Actions

1. **listModels**: List Google Gemini/Imagen models available to the connected API key.
2. **generateImages**: Generate images based on a textual prompt using Imagen 3 model.

## Authentication

- This plugin uses `auth.type = api_key`.
- The user should enable the plugin and paste a Google AI Studio API key when prompted.
- The runtime injects the saved key as a query parameter `key`.

## Usage Notes

- `generateImages` requires a `prompt`.
- Optional parameters like `numberOfImages`, `aspectRatio`, `outputMimeType`, and `personGeneration` can be specified.

## Examples

### Example: Listing Models

```json
{
  "agentId": "123",
  "pluginKey": "com.google.imagen",
  "actionKey": "listModels",
  "connectionKey": "default",
  "params": {}
}
```

### Example: Generating an Image

```json
{
  "agentId": "123",
  "pluginKey": "com.google.imagen",
  "actionKey": "generateImages",
  "connectionKey": "default",
  "params": {
    "prompt": "A futuristic city in the style of cyberpunk, ultra detailed, 8k",
    "numberOfImages": 1,
    "aspectRatio": "16:9",
    "outputMimeType": "image/png"
  }
}
```

If the plugin is not authorized yet, ask the user to enable the Google Imagen plugin and fill in the API key before invoking actions.
