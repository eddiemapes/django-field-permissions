# Claude Code Instructions

## Project Overview

This is a reusable Django package for creating field-level permissions for database model fields. The two access levels are: read and edit. Field-level permissions can be applied on the user or the group level.
The package name is django-field-permissions. The internal django app name is field_permissions.

## Reference Repository
The primary repository to reference for existing field-level permissions code is located at C:\Users\Eddie Mapes\Desktop\Vetting App
The key files in this repository to reference are:
- vetapp/settings.py
- vetapp/environment_processor.py
- crm/views/permissions.py
- crm/models.py

Anything outside of these files can be ignored unless absolutely needed.

## Tech Stack

- Django (Python)

## Code Style & Conventions

- Follow existing patterns in the codebase before introducing new ones
- Use Django function-based views
- Do not use any nested functions
- Use python f strings rather than parameterized strings

## Behavior Guidelines

- Do not refactor or clean up surrounding code when fixing a bug or adding a feature without explicit approval
- Do not introduce new dependencies without explicit approval

## Branch Strategy

- Main integration branch: `main`

## Reference Docs
- Package purpose and app structure: read docs/OVERVIEW.md
- System architecture and component interactions: read docs/ARCHITECTURE.md