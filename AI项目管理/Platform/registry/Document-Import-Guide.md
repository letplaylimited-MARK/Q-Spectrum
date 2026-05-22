# Document Import Guide

## Purpose

This script scans the current Markdown knowledge base and emits structured document records for later insertion into PostgreSQL.

It scans only the folders listed in this guide and only files matching `*.md`.

## Covered folders

- `Skills/`
- `Maps/`
- `QCM/`
- `Systems/`
- `Platform/`
- `roles/`

## Output

JSON records with:

- `title`
- `document_type`
- `file_path`
- `content_hash`

`file_path` is emitted as an absolute filesystem path.
