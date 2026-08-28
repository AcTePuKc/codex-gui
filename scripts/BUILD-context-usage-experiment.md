# Build command

From the repository root on Windows:

```powershell
cd .\codex-rs
cargo build --release -p codex-cli
```

The expected binary is:

```text
codex-rs\target\release\codex.exe
```

Then return to the repository root and launch it with:

```powershell
.\scripts\run-context-usage-experiment.ps1 `
  -CodexExe ".\codex-rs\target\release\codex.exe" `
  -WorkingDirectory "<small-test-repository>"
```
