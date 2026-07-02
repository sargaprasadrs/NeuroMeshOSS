# Contributing to NeuroMeshOSS

First off, thank you for taking the time to contribute! Contributions are what make the open-source community such an amazing place to learn, inspire, and create.

## How Can I Contribute?

### Reporting Bugs

* Check if the issue has already been reported in the GitHub Issues list.
* If not, open a new issue using our **Bug Report** template, providing details, reproducible steps, and logs.

### Submitting Pull Requests

1. **Fork the Repository:** Create a personal fork of the project on GitHub.
2. **Clone the Repo:** Clone the fork to your local machine:
   ```bash
   git clone https://github.com/YOUR_USERNAME/NeuroMeshOSS.git
   ```
3. **Set up Dev Environment:**
   ```bash
   make init
   ```
4. **Create a Branch:** Create a branch for your work:
   ```bash
   git checkout -b feature/my-new-feature
   ```
5. **Implement & Test:** Keep changes focused, run tests via `make test`, and lint using `make lint`.
6. **Commit Changes:** Adhere to clean commit messaging conventions.
7. **Submit PR:** Push your branch and open a PR using our Pull Request template.

## Coding Style Standards

- **Strict Typing:** All Python additions must pass `mypy` strict type checking.
- **Ruff Compliance:** All Python files must be formatted and linted with `ruff`.
- **Frontend Formatting:** Frontend edits must pass `eslint` and `prettier` checks.
- **Hexagonal Architecture:** Maintain clean separation between `core/ports` and infrastructure `adapters`. Core modules must have no external framework imports.
