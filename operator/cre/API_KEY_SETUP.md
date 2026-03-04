# OpenAI API Key Setup

## Quick Setup

The CoVT test reads the API key from the environment variable `OPENAI_API_KEY`.

### Option 1: Set for Current Session (Temporary)

```bash
export OPENAI_API_KEY='your-api-key-here'
```

Then run the test:
```bash
cd /Users/christianpardo/rust
PYTHONPATH=/Users/christianpardo/rust/operator python3 operator/cre/test_excalidraw_covt.py
```

### Option 2: Set Permanently in Shell Profile (Recommended)

Add to your `~/.zshrc` (since you're using zsh):

```bash
echo 'export OPENAI_API_KEY="your-api-key-here"' >> ~/.zshrc
source ~/.zshrc
```

### Option 3: Create a Local Config File (Alternative)

If you prefer not to use environment variables, you can create a config file:

**File:** `/Users/christianpardo/rust/operator/cre/.env`

```bash
OPENAI_API_KEY=your-api-key-here
```

Then modify the test script to load from `.env` file (requires `python-dotenv` package).

---

## How It's Currently Used

The `VLMCoordinator` class reads the API key in this order:

1. **Constructor parameter** (`api_key` argument)
2. **Environment variable** (`OPENAI_API_KEY`)
3. **Raises error** if neither is found

**Code location:** `operator/vlm_coordinator.py` lines 107-112

```python
self.api_key = api_key or openai.api_key if hasattr(openai, 'api_key') else None
if not self.api_key:
    import os
    self.api_key = os.getenv("OPENAI_API_KEY")
if not self.api_key:
    raise RuntimeError("OpenAI API key required...")
```

---

## Recommended Approach

**Use Option 2** (add to `~/.zshrc`) for permanent setup:

```bash
# Add to ~/.zshrc
export OPENAI_API_KEY='sk-your-actual-key-here'

# Then reload
source ~/.zshrc

# Verify it's set
echo $OPENAI_API_KEY
```

---

## Security Note

⚠️ **Never commit your API key to git!**

If you create a `.env` file, make sure it's in `.gitignore`:
```bash
echo "operator/cre/.env" >> .gitignore
```
