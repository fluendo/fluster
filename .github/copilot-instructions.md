# Generic Copilot Instructions

These instructions are intended for GitHub Copilot and similar AI coding assistants. They provide general best practices and coding standards that can be applied to any Fluendo's software project.

## Coding Standards
- Follow the existing code style (brace placement, indentation, naming conventions, comments, documentation, etc.).
- Use descriptive variable and function names, following ruff and mypy rules.
- Add comments for non-obvious logic.
- Prefer readability over micro-optimizations for non-critical code.
- Write modular, reusable functions.
- Avoid large functions; break them into smaller units.
- Handle errors gracefully, checking return values of functions.
- Add appropriate logging where needed.
- Use Doxygen-style or project-standard comments for public APIs and entry points.
- Refer to project or ecosystem coding standards and best practices if in doubt.

## Compatibility
- Ensure code is portable across supported platforms.
- Use appropriate compiler flags and options to ensure compatibility.
- Use APIs correctly, following their documentation and best practices.
- Ensure new code adheres to project development guidelines.

## Continuous Integration and Testing
- CI should validate pull requests and main branch changes by running the full build and test suite.
- Ensure all tests pass before submitting changes.
- Update the build system and CI configuration if you add new components or tests.
- Add new tests to the test directory and include them in the build.
- Always validate changes with the full test suite and CI.

## File Structure and Organization
- Place new or modified code in the appropriate subdirectory.
- Use or extend libraries for shared logic.
- Use project documentation for additional details.
- Only perform a search if the information in these instructions is incomplete or found to be in error.

## Security and Confidentiality
- Do not generate or suggest code for proprietary, confidential, or security-sensitive algorithms.
- Review all generated code for vulnerabilities, especially in buffer handling, file I/O, and network operations.
