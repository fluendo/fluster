# Generic Git Commit Instructions

These guidelines are intended for any software project to ensure that all commits are clear, actionable, and maintainable. Follow these instructions for every commit and pull request.

## Commit Message Structure
- **Summary line:** Start with a short, descriptive summary (max 72 characters).
- **Issue reference:** If applicable, include the issue or ticket number (e.g., `PROJECT-1234`).
- **Detailed description:** Add a blank line, then provide context, rationale, and details about the change. Include:
  - What was changed and why
  - Any relevant error messages or bug descriptions
  - Implementation notes or side effects

## Best Practices
- Group related changes in a single commit. Avoid mixing unrelated changes.
- Reference affected files or components if not obvious from the context.
- For bug fixes, describe the root cause and how it was resolved.
- For new features, explain the motivation and usage.
- For refactoring, explain the reason and expected impact.
- For documentation, specify what was updated or clarified.
- For CI/build changes, describe the effect on the workflow.
- Prefer writing paragraphs instead of bullet points or enumeration.
- Start the commit title with the main component or module affected, if applicable.

## Examples
```
core: Fix memory leak in buffer handling
A memory leak was found in the buffer allocation logic. This commit ensures all buffers are properly freed after use.

Issue: PROJECT-1234

---

docs: Update API usage examples
Expanded the documentation to include new usage examples for the latest API changes.
```

## Additional Guidelines
- Use tags for releases and versioning as appropriate.
- Keep commit messages in English.
- Proofread messages for clarity and completeness.
- If reverting, reference the original commit and explain why.
- For WIP (work in progress), clearly mark the commit and avoid merging to main branches.
