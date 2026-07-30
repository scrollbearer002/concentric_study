# Personal Cursor Control Plane

Captured 2026-07-30 from the local Mac and the current Cursor session. This is an inventory of Christian's actual control surfaces and trust boundaries, not a feature catalog.

## Current shape

```text
Christian
├── Local Mac
│   ├── Cursor Desktop 3.13.25 (arm64)
│   ├── local Agent/IDE sessions
│   ├── repository + local filesystem
│   ├── macOS TCC permissions
│   ├── ~/.cursor configuration
│   └── local/browser MCP processes
├── Cursor account surfaces
│   ├── cursor.com dashboard
│   ├── account/team policy and Privacy Mode
│   ├── integrations and MCP
│   └── Cloud Agent environments, secrets, and network policy
└── Remote execution
    └── isolated Cloud Agent VMs with repository copies and separately scoped access
```

The essential boundary is local versus cloud. A local session can inspect this Mac only to the extent allowed by the current process, filesystem permissions, sandbox, approval policy, and TCC. A Cloud Agent runs in a Cursor-managed VM and cannot be treated as evidence about this Mac's hardware, packages, applications, or TCC state.

## Account surfaces

The local filesystem proves that Cursor Desktop is installed and configured. It does **not** safely prove the currently signed-in email, subscription, team membership, dashboard Privacy Mode, source-control integration, Cloud Agent secrets, or network allowlist. Those settings must be verified in the authenticated [Cursor dashboard](https://cursor.com/dashboard).

Account-controlled surfaces that matter operationally:

- Personal or team identity and billing/entitlement
- Privacy Mode and data-governance policy
- GitHub/GitLab/Bitbucket/Azure DevOps connection used by Cloud Agents
- Team integrations and MCP marketplace policy
- Cloud Agent environment secrets
- Cloud Agent outbound-network policy and private-network connectivity
- Team follow-up policy, because allowing another user to steer an agent that holds the creator's credentials expands the credential trust boundary

No account identifier, token, secret value, or credential was copied into this file.

## Local runtimes

### Cursor Desktop

- Version 3.13.25, Apple Silicon
- Bundle identifier `com.todesktop.230313mzl4w4u92`
- Embedded `cursor` launcher available
- Current machine can run local IDE/Agent work against the repository and local tools, subject to approvals and macOS permissions

### Cursor CLI

- The standalone `agent` command is not currently on `PATH`.
- `~/.cursor/cli-config.json` exists.
- Its approval mode is `allowlist`.
- It contains one allow entry and no deny entries.
- Sandbox and network configuration objects are present.
- The repository has no `.cursor/cli.json`.

The CLI configuration exists, but the absent executable means it is not currently an available runtime from this shell. If installed later, it should be reviewed before using broad options such as `--force`, `--yolo`, `--approve-mcps`, or `--trust`.

### Cloud Agents

Cloud Agents are remote, isolated virtual machines. They receive a repository copy and whatever integrations, secrets, and network access are configured for the account/environment. They do not inherit this Mac's Homebrew state, applications, Hammerspoon runtime, or TCC database. See [Cloud Agents](https://cursor.com/docs/cloud-agent) and [Cloud Agent security and network](https://cursor.com/docs/cloud-agent/security-network).

## Rules and repository authority

- Repository rule directory: `.cursor/rules`
- Repository rule file: `.cursor/rules/orchestration.mdc`
- Repository-root `AGENTS.md`: absent at capture
- A parent workspace `AGENTS.md` exists outside the repository and is active in this local session.

Rules are instructions, not an operating-system security boundary. They can shape agent behavior but do not replace sandboxing, approvals, filesystem permissions, TCC, source-control review, or secret scoping. Cursor's CLI also reads repository rules and supported instruction files; see [Using Cursor CLI](https://cursor.com/docs/cli/using).

## MCP inventory

### Configuration on disk

- Global config: `~/.cursor/mcp.json`
- Configured global server name: `safari`
- User-settings MCP file under `~/Library/Application Support/Cursor/User/mcp.json`: absent
- Repository `.cursor/mcp.json`: absent

Only server names were read. Commands, arguments, environment variables, URLs, tokens, and OAuth material were deliberately not copied.

### Servers exposed to this Cursor session

The current session advertises these Cursor-managed or user-scoped MCP surfaces:

- `cursor-app-control` — Cursor project/window control
- `cursor-ide-browser` — Cursor-owned browser tab and Chrome DevTools operations
- `user-safari` — automation against the user's Safari session

Session availability is not the same as repository configuration. A server can be injected by Cursor or the user environment even when no project `mcp.json` exists.

### MCP trust rule

Treat each MCP server as code plus credentials crossing a data boundary:

1. Verify the server source and transport.
2. Inventory tools before use.
3. Grant the minimum API scopes.
4. Keep secrets in environment/OAuth storage, never in repository JSON.
5. Prefer local `stdio` for sensitive local integrations when appropriate.
6. Require confirmation for external writes, messages, purchases, permission changes, or destructive actions.
7. Re-evaluate trust when a server, package, command, or endpoint changes.

Cursor's official configuration and security guidance is at [MCP](https://cursor.com/docs/mcp). Cursor CLI uses the editor's MCP configuration and has separate tool approvals; see [CLI MCP](https://cursor.com/docs/cli/mcp) and [CLI permissions](https://cursor.com/docs/cli/reference/permissions).

## macOS trust boundary

Cursor currently has powerful local TCC grants, including Accessibility, Screen Recording, Input Monitoring, event posting, Developer Tool, and Full Disk Access. It can automate several named applications through Apple Events, but QuickTime Player automation is denied and some user-data scopes are denied or limited.

Hammerspoon also has Accessibility, Screen Recording, Input Monitoring, Developer Tool, and Full Disk Access grants.

These grants make local automation possible and raise the consequence of an unsafe prompt, untrusted repository instruction, compromised extension, or malicious MCP server. TCC authorization is capability, not intent verification. Keep approvals and human review in the loop for consequential actions.

## Source-code and execution boundary

- Local sessions operate on the active synchronized repository copy and can encounter uncommitted work from other tools or agents.
- Cloud Agents operate on remote repository snapshots/worktrees and require explicit synchronization through source control or artifacts.
- The active local repository currently has pre-existing modified and untracked files. New work must not assume a clean tree or overwrite unrelated changes.
- The repository's `HostToolHealth` currently reports `all_required_ready: false`; local automation should honor that gate instead of inferring readiness from TCC grants alone.

## Practical control checklist

Before a local automation run:

- Confirm the exact repository path and git state.
- Run `HostToolHealth`.
- Confirm the intended MCP servers and tool scopes.
- Check whether the action is read-only, local write, external write, or destructive.
- Keep private identifiers and credentials out of artifacts and logs.

Before a Cloud Agent run:

- Confirm source-control connection and target branch.
- Confirm Privacy Mode, secrets, and network policy in the dashboard.
- Assume no access to Mac-local state unless explicitly bridged.
- Review generated commits/artifacts before merging or downloading.

Before changing control-plane configuration:

- Record the current state.
- Make the smallest reversible change.
- Do not disable TCC protections, sandboxing, or approval gates merely to make a test pass.

## Official references

- [Cursor dashboard](https://cursor.com/dashboard)
- [Cloud Agents](https://cursor.com/docs/cloud-agent)
- [Cloud Agent security and network](https://cursor.com/docs/cloud-agent/security-network)
- [Privacy and data governance](https://cursor.com/docs/enterprise/privacy-and-data-governance)
- [MCP](https://cursor.com/docs/mcp)
- [Cursor CLI usage](https://cursor.com/docs/cli/using)
- [Cursor CLI MCP](https://cursor.com/docs/cli/mcp)
- [Cursor CLI permissions](https://cursor.com/docs/cli/reference/permissions)
