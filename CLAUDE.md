# Claude Code Project Context
This file provides essential context for Claude Code when working on this project.

## Project Documentation
The following files contain critical project information:
- @docs/prd.md - Product Requirements Document with goals, features, and technical requirements
- @docs/project-guide.md - Discovery guide for existing systems, components, and patterns. **Read this before implementing new functionality** to find what already exists.

### Specialized Documentation
The following documents should be read when working in specific areas:
- `docs/as-built.md` - **Read this document when planning or implementing tools.** Defines architecture, validation requirements, error handling, description standards, and testing requirements for the tool system.

## Development Environment
**Platform**: macOS
When suggesting commands, scripts, or configuration options, **ALWAYS** use macOS-compatible options. Avoid Linux-specific flags or Windows-specific commands.

### Definition of Done
Implementation is complete when:
- All acceptance criteria are met
- All tests pass - no exceptions, no skipped tests
- Minimum 80% code coverage on every file touched in the commit
- No formatter, linter, or type checker issues

### Project Guide Maintenance
**NEVER commit to git without first updating `docs/project-guide.md`** to reflect any changes:
- New systems, modules, or components added
- Systems removed or relocated
- New execution contexts or API endpoints
- New settings categories or key functions

This is a **hard requirement**. If you added, removed, or modified any server systems, components, API endpoints, or settings, the project guide **MUST** be updated in the same commit.
**Before updating the project guide**, read `docs/project-guide-instructions.md` for guidance on what to include and how to maintain consistency.
The project guide is the primary discovery document for finding existing functionality. Keeping it current prevents duplicate implementations and helps integrate with existing patterns.

## Coding Guidelines
### Code Style
- **ALWAYS** use tabs for indentation, not spaces. Ruff is configured to enforce this.
- Focus above all on code readability. Code is read much more than written.
- **NEVER** use leet code or clever code solutions. Clean readable code is the goal.
- **NEVER** comment on what code is doing, instead comment why. If you have to comment what that indicates poor readability.
- **ALWAYS** minimize function/file length and nesting as much as possible.
- **ALWAYS** use descriptive names. There is no advantage to using "i" over "index".
- **ALWAYS** include units in names such as "timeoutSeconds" or "distanceMeters". This avoids unit confusion.
- **NEVER** use magic numbers.
- **ALWAYS** use documentation comments on functions and classes.
- **ALWAYS** keep comments current.
- **NEVER** change "AI NOTE:" comments. These comments are explicitly intended to guide AI agents where they often make mistakes.
- **ALWAYS** use early returns to minimize nesting.

### Assertions
- **ALWAYS** validate function inputs to ensure they meet requirements
- **ALWAYS** validate function outputs when processing could fail to produce correct output
- **ALWAYS** use descriptive assertion messages that explain what was expected

### Error Handling
- **ALWAYS** catch and handle recoverable errors at the appropriate level
- **NEVER** catch errors only to re-throw them to the next level
- Internal functions and classes should throw unrecoverable errors and let them bubble up
- UI components should catch all errors and display them to the user

## Time Handling
### Storage and Internal Processing
- **Use UTC for most internal storage** - Timestamps in the database, logs, and internal APIs should use UTC
- **Use floating time for location-independent events** - Some times have no timezone (e.g., "8:00 AM" means "8:00 AM wherever the user is at that moment"). These should be stored without timezone information.

### LLM Communication
- **ALWAYS normalize times to the user's timezone when presenting to the LLM**
- LLMs do not handle timezone conversions reliably. All times in system prompts, tool outputs, and context should be in the user's local timezone.
- Include the timezone explicitly when relevant (e.g., "3:00 PM PST" not just "3:00 PM")
