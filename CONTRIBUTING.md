# Contributing to Army Randomiser

Thanks for your interest in contributing!

## Local Setup

### 1. Create Your Own Discord Bot (for testing)

You'll need your own bot token to test locally. **Never use the production token.**

1. Go to the [Discord Developer Portal](https://discord.com/developers/applications)
2. Click **New Application** → Name it something like "Army Bot Dev"
3. Go to **Bot** (left sidebar)
4. Click **Reset Token** → Copy the token
5. Enable these **Privileged Gateway Intents** (scroll down):
   - None required for basic functionality
6. Go to **OAuth2** → **URL Generator**
   - Scopes: `bot`, `applications.commands`
   - Bot Permissions: `Send Messages`, `Embed Links`, `Attach Files`, `Use Slash Commands`
7. Copy the generated URL and open it to invite the bot to your test server

### 2. Clone and Configure

```bash
git clone https://github.com/MitchellTLarsen/discord_bot_warhammer.git
cd discord_bot_warhammer
pip install -r requirements.txt
```

Create a `.env` file (this is gitignored):
```
DISCORD_TOKEN=your_bot_token_here
DEV_GUILD_ID=your_test_server_id
```

To get your server ID:
1. Enable Developer Mode in Discord (Settings → App Settings → Advanced → Developer Mode)
2. Right-click your test server → Copy Server ID

### 3. Run Locally

```bash
python bot.py
```

You should see `[DEV MODE] Logged in as YourBot#1234`.

**Dev mode benefits:**
- Commands only appear in your test server (won't conflict with production)
- Command updates are instant (no 1-hour global sync delay)
- Safe to test without affecting production users

---

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
