---
name: "integration-gmail"
description: "Use the Gmail declarative plugin through the plugin gateway."
---

# Gmail Plugin Skill

Use the Gmail plugin by calling the gateway at `http://workbench:3000/plugins/invoke` with:

- `agentId`: the current agent id
- `pluginKey`: `com.google.gmail`
- `actionKey`: one of the actions listed below
- `connectionKey`: optional, defaults to `default`
- `params`: action input parameters

## Available Actions

1. **getProfile**: Call to verify the account connection after authorization.
2. **listMessages**: Search or list message IDs and thread IDs matching a query.
3. **listThreads**: Search or list conversation threads matching a query.
4. **getMessage**: Retrieve a single message details (body, headers, snippets, etc.) using `id`.
5. **getThread**: Retrieve conversation thread detail using `id`.
6. **sendMessage**: Send a new email. Requires a base64url encoded RFC 2822 MIME message string.
7. **trashMessage**: Move a message to the trash folder using `id`.
8. **untrashMessage**: Move a message out of the trash folder using `id`.
9. **archiveMessage**: Archive a message (removes the `INBOX` label).
10. **markAsRead**: Mark a message as read (removes the `UNREAD` label).
11. **markAsUnread**: Mark a message as unread (adds the `UNREAD` label).
12. **starMessage**: Star a message (adds the `STARRED` label).
13. **unstarMessage**: Unstar a message (removes the `STARRED` label).

## How to Send Emails (`sendMessage`)

To send an email, construct a standard RFC 2822 email format as a plain text string:

```text
To: recipient@example.com
Subject: Your Subject Here
Content-Type: text/plain; charset="UTF-8"

Your email body content goes here.
```

Encode the entire RFC 2822 string into **Base64url** (URL-safe Base64: replace `+` with `-`, `/` with `_`, and remove any `=` padding). Pass the encoded string as the `raw` parameter under `params`.

## Encoding Rules and Common Pitfalls

- Treat Gmail `sendMessage` as requiring a fully valid RFC 2822 MIME message before Base64url encoding.
- Do not place raw non-ASCII text directly in mail headers such as `Subject`, `From`, or display-name parts of `To`, `Cc`, and `Bcc`.
- If a header contains Chinese or any other non-ASCII characters, encode that header value using **RFC 2047 encoded-word** syntax before building the final RFC 2822 message.
- Safe pattern:
  - ASCII-only headers may be written directly.
  - Non-ASCII header values should be encoded first, then inserted into the header line.
- The body may contain UTF-8 text, but the MIME part must declare charset explicitly, for example `Content-Type: text/plain; charset="UTF-8"`.
- When sending a UTF-8 body, prefer adding a matching `Content-Transfer-Encoding` such as `base64` or `quoted-printable` when needed, instead of assuming raw 8-bit text will render correctly everywhere.
- If you are unsure whether a string is pure ASCII, treat it as non-ASCII and encode the header value first.

### Header Encoding Example

Incorrect:

```text
Subject: 你好，这是测试邮件
```

Correct pattern:

```text
Subject: =?UTF-8?B?...base64-encoded-header...?
```

The final `raw` payload must contain the already-encoded RFC 2822 message, not a mix of raw Chinese headers and later Base64url wrapping.

## Reading Messages and Attachment Text Safely

- Do not assume message bodies, attachment text, CSV files, or exported text files are UTF-8 just because they contain readable text.
- If text looks garbled, first inspect MIME metadata such as `Content-Type` charset and `Content-Transfer-Encoding`.
- Decode in this order:
  1. Apply the declared transfer encoding such as `base64` or `quoted-printable`.
  2. Decode bytes using the declared charset if present.
  3. If charset is missing and the text is still garbled, try common fallbacks such as `UTF-8`, `GB18030`, `GBK`, or `Big5` based on the visible language context.
- If a header itself looks garbled, check whether it is an RFC 2047 encoded-word and decode it before judging the content.
- When reading attached text files, do not claim the file content is corrupted until charset and transfer-encoding mismatches have been ruled out.
- If decoding is uncertain, report that the current text may be mojibake caused by charset mismatch and explain which charset assumptions were tried.

## Examples

### Example: Searching Messages
```json
{
  "agentId": "123",
  "pluginKey": "com.google.gmail",
  "actionKey": "listMessages",
  "connectionKey": "default",
  "params": {
    "q": "from:openai newer_than:7d",
    "maxResults": 10
  }
}
```

### Example: Sending Email
```json
{
  "agentId": "123",
  "pluginKey": "com.google.gmail",
  "actionKey": "sendMessage",
  "connectionKey": "default",
  "params": {
    "raw": "VG86IHJlY2lwaWVudEBleGFtcGxlLmNvbQpTdWJqZWN0OiBZb3VyIFN1YmplY3QgSGVyZQpDb250ZW50LVR5cGU6IHRleHQvcGxhaW47IGNoYXJzZXQ9IlVURi04IgoKWW91ciBlbWFpbCBib2R5IGNvbnRlbnQgZ29lcyBoZXJlLg"
  }
}
```

### Example: Marking Message as Read
```json
{
  "agentId": "123",
  "pluginKey": "com.google.gmail",
  "actionKey": "markAsRead",
  "params": {
    "id": "18f4a13e2f5b4d90"
  }
}
```

If the plugin is not authorized yet, ask the user to enable the Gmail plugin and complete OAuth before invoking actions.
