# AI Jury API Keys

The AI jury uses **different keys than the executor**. Do not reuse your Gemini key for the jury.

## Two keys for the jury

| Key | Provider | Role | Where to get it |
|-----|----------|------|-----------------|
| **`ANTHROPIC_API_KEY`** | Anthropic | Claude as judge | [console.anthropic.com](https://console.anthropic.com) → API Keys → generate. Pay-as-you-go; no subscription. |
| **`OPENAI_API_KEY`** | OpenAI | GPT-4o as second judge | [platform.openai.com](https://platform.openai.com) → API Keys → generate. Same deal. |

- **Claude (Anthropic):** ~\$0.003 per packet reviewed.
- **GPT-4o (OpenAI):** ~\$0.005 per packet (vision calls).

For the current 6 packets, a full two-judge jury run is about **\$0.05 total**. Effectively free.

## Single key to start

If you only want one key at first, use **Anthropic**. Claude is strong at visual reasoning and chain-of-thought evaluation. Run with:

```bash
--judges claude
```

You still get rubric decomposition, self-critique, and calibration tracking — only the cross-validation debate round is skipped. Add `OPENAI_API_KEY` later when you want full two-judge cross-validation.

## Why not Gemini for the jury?

Your **Google Gemini API key** is what the **executor** (the agent) already uses. The jury deliberately does **not** use Gemini: the point of the heterogeneous jury is to avoid shared blind spots. Same model family as the executor would mean the judge could share the same failures. So: **Anthropic key to start; OpenAI key when you want full two-judge cross-validation.** Both are short signups (on the order of five minutes).

## Quick reference

- **Executor (agent):** `GEMINI_API_KEY` (or `OPENAI_API_KEY` in some paths) — vision, planning, actions.
- **Jury:** `ANTHROPIC_API_KEY` (Claude judge), `OPENAI_API_KEY` (GPT-4o judge). Use `--judges claude` or `--judges gpt4o` for a single judge.

See **SECTION_8_VERIFICATION_GATE_CALIBRATION.md** §5.1 for first run and bootstrap trust.
