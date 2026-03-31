# Project Guide Maintenance Instructions

This document explains how to maintain `docs/project-guide.md`. Read this before making updates.

## Purpose

The project guide exists for **discovery** - helping find what systems exist before implementing
new functionality. It is NOT documentation of how systems work (that's what LSP and reading code are for).

## What to Include

### Directory Structure
- Folder-level organization only (not individual files)
- Brief annotations explaining what each folder contains
- Update when new folders are added or folder purposes change

### Server Systems
- Each major system with its location and purpose
- Entry points (the file you'd start reading)
- Key functions that other code calls into
- Update when new systems are added or key functions change

### Components
- Component name and one-line purpose
- Grouped by category (settings, chat, core, layout, etc.)
- Update when new reusable components are added

### API Endpoints
- Endpoint path, input shape, purpose
- Update when new endpoints are added

### Patterns for Adding Functionality
- Brief checklist of steps for common extension patterns
- Update when new extension patterns emerge

## What NOT to Include

- **Individual file listings** - LSP handles this
- **Export listings** - LSP handles this
- **Implementation details** - Reading code handles this
- **How systems work** - Reading code handles this
- **Generic framework conventions** - Only project-specific patterns

## Update Process

Before committing, review your changes and update the relevant section of project-guide.md.
Match the existing format. Keep it minimal and scannable.

## Format Guidelines

- Use relative paths from the project root
- List key functions that external code calls, using code formatting: `functionName()`
- Use tables for lists of similar items (systems, components, endpoints)
- Keep descriptions to one line
