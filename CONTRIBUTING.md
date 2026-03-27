# Contributing to Army Randomiser

Thanks for your interest in contributing!

## How to Contribute

1. **Fork the repository** (or create a branch if you have access)
2. **Create a feature branch** from `main`:
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. **Make your changes**
4. **Test locally**:
   ```bash
   python bot.py
   ```
5. **Commit your changes**:
   ```bash
   git commit -m "Add: description of your change"
   ```
6. **Push to your branch**:
   ```bash
   git push origin feature/your-feature-name
   ```
7. **Open a Pull Request** against `main`

## Pull Request Requirements

- All CI checks must pass (linting, syntax checks)
- Code owner approval required
- Clear description of what changed and why

## Branch Naming

- `feature/` - new features
- `fix/` - bug fixes
- `docs/` - documentation updates
- `refactor/` - code refactoring

## Code Style

- Follow existing code patterns
- Keep functions focused and reusable
- No hardcoded secrets or tokens

## Adding/Updating Factions

Faction data lives in `factions/*.json`. See existing files for format.

## Questions?

Open an issue if you have questions or suggestions.
