# Contributing to CoreTex

Thank you for your interest! Here, *everyone*  is welcome to contribute their ideas and code.

Please have patience with the (singular) maintainer of CoreTex as this is his first time maintaining a repo let alone an OSS project. Help is welcome!

I've set forth this contributing standard to make sure we're all on the same page and CoreTex can evolve.

## Code of Conduct

By participating in CoreTex, you agree to abide by our [Code of Conduct](CODE_OF_CONDUCT.md). Please report any unacceptable or cruel behavior to CoreTex's maintainers.

## How Can I Contribute?

### 1. 🐛 Reporting Bugs
Before creating a new bug report, please check the existing open issues to see if the problem has already been flagged.

When opening a new bug issue, please include:
* **Clear Summary**: A concise descriptive overview of the problem in the title.
* **Reproduction Steps**: A step-by-step list of instructions to reproduce the unexpected behavior.
* **Environment Details**: Target OS, runtime engine versions, and any active configuration flags.
* **Results**: Explicitly state the expected vs. actual results, including full stack traces or terminal output logs.

### 💡 2. Suggesting Enhancements
We love new ideas! To suggest an enhancement or architectural refactor:
1. Open an issue describing the proposed feature or modification.
2. Explain the core use case, technical value, and why this addition benefits the overall project ecosystem.
3. Provide examples, pseudo-code blocks, or architectural sketches if relevant.

### 3. 🔧 Submitting Code (Pull Requests)
To contribute code fixes or new features, please adhere to the following git workflow:

> **Tip:** Always align your branch changes with our automated Pull Request template before submission.

1. **Fork the Repository**: Create a personal fork of the project on your Git account.
2. **Clone Locally & Branch**: Clone your fork and create a descriptive branch name tracking your changes:
   * For features: `feature/your-feature-name`
   * For bug fixes: `fix/your-bug-name`
3. **Implement & Test**: Write your modifications and ensure they are covered by automated test suites.
4. **Run Code Quality Checks**: Confirm your code passes all local workspace formatting, style, and linting guidelines.
5. **Commit Cleanly**: Write clear, concise commit messages (preferably matching the Conventional Commits specification).
6. **Push & Open a Pull Request**: Push your branch to your personal fork and submit a Pull Request against our main repository branch.

---
## 📐 Style & Architecture Guidelines

To maintain code quality and prevent technical debt, all incoming changesets must meet these engineering baselines:

* **Code Formatting**: Ensure your code is properly formatted according to the project's configurations before staging files.
* **Type Safety**: Avoid untyped interfaces. Use explicit type annotations where required by the project's tooling constraints.
* **Documentation**: Update corresponding README notes or add clear inline documentation comments for any complex or asynchronous control blocks.
* **Testing Expectations**: Every new logic branch, utility helper, or component modification must be backed by unit tests. Existing automated tests must continue to pass without hanging, deadlocking, or introducing dynamic race conditions.
