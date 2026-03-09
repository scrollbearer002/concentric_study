# Web Auth And Proton Pass Generalization (PhD)

## Executive claim

The correct way to generalize from one successful website benchmark to "any
website" is **not** to reuse one site script everywhere. It is to extract the
latent capability families that recur across websites, then route credential
operations through an approved provider path with explicit human approval at
every secret boundary.

That is now the implemented direction in this repo.

## Why the QA Practice result is not enough by itself

The successful QA Practice run at
[qa_practice_mastery_summary.json](/Users/christianpardo/Desktop/concentric_study/operator/cre/runs/dbc28d8654b5/qa_practice_mastery_summary.json)
proves that the Safari/macOS substrate can survive heterogeneous UI patterns.
It does **not** by itself prove universal website competence.

The benchmark literature is clear on this point:

- `Mind2Web` argues that web-agent generalization must be evaluated across
  diverse real websites rather than a single narrow environment:
  <https://arxiv.org/abs/2306.06070>
- `WebArena` formalizes cross-site, long-horizon capability evaluation:
  <https://arxiv.org/abs/2307.13854>
- `VisualWebArena` shows that screenshot-grounded agents need multimodal
  benchmarks when layout, rendering, and interaction semantics matter:
  <https://arxiv.org/abs/2401.13649>

Inference from those sources:
the project should generalize by **capability family** and **state-routing
discipline**, not by copying selectors or page-specific click paths.

## What must transfer across websites

The transferable unit is a family of auth and interaction situations:

1. Existing-account login
2. New-account signup plus immediate credential persistence
3. Password reset request
4. Password change and credential rotation
5. 2FA / TOTP challenge
6. Passkey enrollment and use
7. Dynamic DOM mutation after action
8. Shadow DOM / iframe / popup switching

This is captured in
[web_auth_generalization_matrix.json](/Users/christianpardo/Desktop/concentric_study/operator/cre/artifacts/web_auth_generalization_matrix.json).

## Why Proton Pass belongs in the plan

For the user requirement here, Keychain alone is insufficient. The project must
reason about a browser password manager because the desired real workflow is:

- open a site
- recognize login or signup state
- retrieve the right credential from Proton Pass for an existing profile
- or generate and save a new credential in Proton Pass for a new profile

Official Proton docs support the relevant surfaces:

- Browser extension login-management path:
  <https://proton.me/support/pass-browser-extension>
- Save or create login items:
  <https://proton.me/support/save-login-pass>
- Hide-my-email aliases:
  <https://proton.me/support/proton-pass-hide-my-email-alias>
- Passkey support:
  <https://proton.me/support/pass-use-passkeys>
- TOTP / authenticator support:
  <https://proton.me/support/pass-2fa-authenticator>

These sources imply the right project abstraction:
**Proton Pass should be a governed credential-provider path, not a hardcoded
site-specific hack.**

## Implemented repo changes

### 1. Site-independent auth-surface classifier

Added
[auth_workflow.py](/Users/christianpardo/Desktop/concentric_study/operator/security/auth_workflow.py),
which classifies pages from generic cues:

- email / username fields
- password / confirm-password fields
- current-password fields
- passkey prompts
- verification-code prompts
- signup/login/reset copy

It does not rely on one site's selectors.

### 2. Credential workflow router

The same module now plans the correct workflow family:

- `existing_credential_login`
- `new_account_signup_and_save`
- `credential_rotation`
- `credential_recovery`
- `secondary_factor_auth`
- `passkey_enrollment`

This is how the agent decides **when** a password manager should be used and
**which operation** should occur.

### 3. Stronger secret boundary

Expanded
[credential_vault.py](/Users/christianpardo/Desktop/concentric_study/operator/security/credential_vault.py)
so the HITL layer now explicitly treats the following as sensitive:

- `retrieve_password_manager_secret`
- `save_password_manager_secret`
- `create_password_manager_login`
- `generate_password`
- `retrieve_totp_code`
- `create_passkey`

This is the right boundary for a non-toy system. Secret reads, secret writes,
and credential creation are not ordinary clicks.

### 4. Executable tests

Added
[test_auth_workflow.py](/Users/christianpardo/Desktop/concentric_study/operator/cre/test_auth_workflow.py)
to verify:

- login surface recognition
- signup surface recognition
- 2FA surface recognition
- Proton Pass routing for existing-account login
- Proton Pass routing for new-account signup and save
- passkey routing
- HITL enforcement on password-manager reads and writes

## What this enables

The project can now represent the following claim more honestly:

It has a **website-independent auth reasoning layer**.

That is materially stronger than "it passed one website."

Specifically, the system can now distinguish:

- when a page is probably login versus signup
- when credential retrieval is appropriate versus dangerous
- when new-password generation and save is the correct operation
- when passkeys or TOTP are in play
- when the task must remain human-approved even if the UI is automatable

## What it still does not prove

It does not yet prove that the live system can operate Proton Pass on every
real website without failure.

That stronger claim requires a second empirical phase:

1. run a multi-site auth benchmark using these capability families
2. include positive controls and negative controls
3. test existing-login, signup-save, 2FA, and passkey cases
4. measure routing correctness, provider correctness, and secret-boundary discipline

## Correct next step

The next scientifically valid move is:

build a **cross-site auth benchmark branch** around these families, not another
single-site mastery script.

That is how the project learns something that can actually transfer.
