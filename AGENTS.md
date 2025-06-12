# Rust/codex-rs

In the codex-rs folder where the rust code lives:

- Never add or modify any code related to `CODEX_SANDBOX_NETWORK_DISABLED_ENV_VAR`. This variable is automatically set to `0` during `shell` tool execution to explicitly allow network access. A value of `1` disables networking, and some test logic uses this to skip tests that require internet. Changing this behavior will break assumptions made throughout the codebase.

# Mirrored Upstream Projects

`codex-cli/` and `codex-rs/` are synchronized mirrors of upstream repositories. These directories should only be updated by automated tooling. **Do not modify or rebuild them** unless explicitly instructed.

Only `gui_pyside6/` is actively developed in this repo.
