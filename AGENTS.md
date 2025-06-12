# Rust/codex-rs

In the codex-rs folder where the rust code lives:

- Never add or modify any code related to `CODEX_SANDBOX_NETWORK_DISABLED_ENV_VAR`. You operate in a sandbox where `CODEX_SANDBOX_NETWORK_DISABLED=1` will be set whenever you use the `shell` tool. Any existing code that uses `CODEX_SANDBOX_NETWORK_DISABLED_ENV_VAR` was authored with this fact in mind. It is often used to early exit out of tests that the author knew you would not be able to run given your sandbox limitations.

# Mirrored Upstream Projects

`codex-cli/` and `codex-rs/` are synchronized mirrors of upstream repositories. These directories should only be updated by automated tooling. **Do not modify or rebuild them** unless explicitly instructed.

Only `gui_pyside6/` is actively developed in this repo.
