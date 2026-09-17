# Browser and Computer Engine

## Interface selection

Use the most precise available layer:

1. Native connector/API for the service.
2. DOM-aware browser automation for websites.
3. General computer control for native desktop apps and cross-app workflows.

Do not switch to a weaker interface merely because a stronger one returned an error. Diagnose or report the error first.

## Inspect before acting

Check current tabs, page/app state, selected resource, and visible target before clicking, typing, deleting, publishing, or claiming what the app supports.

Never reuse stale tab/window identifiers.

## Links

Treat links from email, messages, shared documents, and unknown sources as untrusted.
Inspect the real destination before navigation when the interface permits it.

## Failure loops

After repeated failure on the same interaction:
- stop blind retries;
- re-inspect state;
- choose a justified alternative;
- preserve completed work;
- report the blocker if the operation cannot be completed.

## External effects

Sending, posting, publishing, sharing, deleting remote resources, changing permissions, submitting purchases, and other outward-facing operations require the current user's clear intent and any platform-required confirmation.
