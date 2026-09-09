# Contributing to Astral Agent

Thank you for your interest in contributing to this project! It is maintained with
care, and every contribution is genuinely appreciated.

## Ways to Contribute

There are many ways to take part:

- **Report bugs** — use the issue template to describe what broke
- **Submit pull requests** — send a PR with a fix or a new feature
- **Write documentation** — help make the project docs clearer
- **Offer ideas** — share suggestions for future development

## The Contribution Process

### 1. Fork the repository

Click the "Fork" button on this repository's page to create a copy under your GitHub
account. Please note: a fork here is a vehicle for proposing changes, **not** a way to
republish this project (see `LICENSE`).

### 2. Create a new branch

Branch from `main` and use a descriptive name:

```bash
git checkout main
git pull origin main
git checkout -b feature/your-feature-name
```

### 3. Make your changes

Implement the change, follow the existing coding style, and add relevant test cases
where you can.

### 4. Run the tests

Make sure the whole suite passes before opening a PR:

```bash
pytest tests/
```

### 5. Open a pull request

- Make sure your branch is up to date with `main`
- Fill in the PR template and explain what you changed
- Link the relevant issue number, if there is one

## Coding Style & Conventions

### Variable and function names

Use descriptive, consistent names:

```python
# Good
def calculate_total_cost(items):
    return sum(item.price * item.quantity for item in items)

# Bad
def calc():
    x = 10
    y = 20
    return x + y
```

### Code formatting

Use an appropriate formatter so the style stays consistent with the rest of the
project.

## Bug Reports

If you find a bug, open an issue that covers:

- **Description** — what happened and what you expected instead
- **Steps to reproduce** — the exact steps that trigger the bug
- **Environment** — OS, Python, and dependency versions
- **Screenshots or logs** — attach them where possible

## Pull Request Template

```markdown
### Description of changes
[Explain what you changed and why]

### Checklist
- [ ] Tests pass
- [ ] Code style follows the project standard
- [ ] No new errors or warnings
- [ ] Documentation updated where needed

### Linked issue (if any)
#XXXX
```

## License

Astral is **not** open source. It is published as a portfolio / personal-use project
under the [Astral Source-Available License (View-Only)](../LICENSE), which means the
code may be read and studied but not redistributed or republished.

Contributions are still welcome. By submitting one you confirm that you have the right
to offer it, and — as set out in `LICENSE` — the maintainer may use and relicense
accepted contributions as part of the project. Please do not submit code you did not
write, or code whose license is incompatible with those terms.

## Contact

Questions or discussion? Reach out through:

- **GitHub Issues** — open a new issue on this repository
- **Email** — albaninurriziq@gmail.com

---

Thank you for helping make Astral better.
