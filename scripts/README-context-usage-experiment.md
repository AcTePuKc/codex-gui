# Running the context-usage experiment on Windows

These helper scripts are intentionally separate from the normal Codex installation.

## 1. Build the fork locally

From the repository root, build the Rust CLI in the `codex-rs` workspace using the project's normal Rust toolchain. Keep the resulting executable separate from any installed Codex binary.

## 2. Launch the instrumented binary

```powershell
.\scripts\run-context-usage-experiment.ps1 `
  -CodexExe "<path-to-your-built-codex.exe>" `
  -WorkingDirectory "<small-test-repository>"
```

The launcher sets `RUST_LOG` so the experiment's `info` tracing target is enabled without changing Codex configuration.

## 3. Collect instrumentation lines

After the controlled run exits:

```powershell
.\scripts\context-usage-experiment.ps1 `
  -Output .\context-usage-experiment.log
```

Keep the controlled run small and stop it if the 5-hour quota begins moving unexpectedly quickly. The experiment branch does not modify context retention or quota behavior; it only records aggregate prompt composition.
