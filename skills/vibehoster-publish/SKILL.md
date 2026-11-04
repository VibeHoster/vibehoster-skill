---
name: vibehoster-publish
description: Check and publish an existing static website to VibeHoster using its connected MCP tools. Use when the user asks to publish or update their project on VibeHoster.
---

# Publish to VibeHoster

Inspect the project locally first. Determine whether its real production output is static, whether a build is needed, and whether runtime functions depend on a server, database, external API, secrets, or server rendering. Do not infer compatibility from the framework name alone. Explain material limitations and propose options; ask before changing the project's behavior or architecture.

Use only the built output intended for public hosting. A user's request to publish authorizes publication of the compatible site; identify meaningful limitations and unexpected potentially sensitive content before uploading. Never include `.env` files, credentials, local databases, source maps, repository metadata, private project data, or server-only code. Client-side files can themselves contain embedded secrets; inspect for them and stop if found. Do not claim an automated scan proves that a build is secret-free.

Run project install/build commands under the user's environment and approval rules. Use `scripts/package_static.py` on the chosen output directory to create a ZIP outside that directory. It refuses unsupported formats, symlinks, hidden files, missing root `index.html`, and uploads beyond platform limits rather than silently dropping files. If packaging fails, explain the cause; do not alter site functionality silently to make it pass.

Let the MCP client handle its own OAuth browser flow. Do not reopen the authorization page or a `127.0.0.1` callback in another browser; wait for the client and verify the connection through an MCP tool. If authentication fails, start a new login flow.

Use the connected VibeHoster MCP tools to authenticate and call `prepare_upload` with the project name and, only for an explicitly selected existing project, its ID. The result includes a short-lived one-use upload ticket. Send the prepared ZIP using `scripts/upload_static.py`, passing that ticket via standard input rather than command-line arguments; do not place it in user-facing messages or logs. Set `VIBEHOSTER_UPLOAD_URL` to the returned upload URL if it differs from the default. The helper streams the archive directly, so its contents need not enter the model context. The helper accepts the production VibeHoster endpoint and local development endpoints only. If the server or required operation is unavailable, say what is missing and stop. Do not request passwords or access tokens in chat.

After publishing, check the resulting URL and report it along with what was and was not verified. A successful HTTP response alone does not prove forms, external APIs, or business logic work. Republishing an existing project may replace edits made on the platform; warn and obtain agreement when that risk applies.
