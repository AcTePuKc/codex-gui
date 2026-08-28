# Context usage instrumentation experiment

This branch is a diagnostic fork used to investigate openai/codex#41369.

It intentionally does **not** change prompt construction, context retention, compaction, tool execution, retry behavior, or quota handling. The only behavioral addition is an aggregate tracing event emitted when a `Prompt` is formatted for a model request.

Tracing target:

```text
codex_core::context_usage_experiment
```

Message:

```text
context usage experiment prompt
```

The event contains only aggregate sizes/counts. It does not log prompt text, source code, tool output contents, commands, credentials, or other request content.

## Key fields

- `sequence`: process-local monotonically increasing formatting sequence.
- `input_items`: number of model-visible `ResponseItem`s.
- `input_estimated_tokens`: Codex's existing per-item coarse model-visible token estimator summed over the actual formatted request input.
- `user_message_tokens`, `developer_message_tokens`, `assistant_message_tokens`, `other_message_tokens`: input estimate split by message role.
- `reasoning_tokens`: estimated retained reasoning items.
- `tool_call_tokens`: estimated retained tool-call items.
- `tool_output_count`: number of retained tool outputs.
- `tool_output_tokens`: estimated tokens in all retained tool outputs.
- `recent_tool_output_tokens`: estimated tokens in the four newest retained tool outputs.
- `old_tool_output_tokens`: all retained tool-output estimate excluding those four newest outputs.
- `largest_tool_output_tokens`: largest retained tool output estimate.
- `compaction_tokens`: retained compaction/context-compaction estimate.
- `agent_message_tokens`, `additional_tools_tokens`, `other_tokens`: other retained item categories.
- `tool_count`: number of tools advertised with the prompt.
- `tool_schema_bytes`, `tool_schema_estimated_tokens`: serialized tool-schema size and a labeled 4-bytes/token coarse estimate.
- `base_instruction_bytes`, `base_instruction_estimated_tokens`: base-instruction text size and a labeled 4-bytes/token coarse estimate.
- `use_responses_lite`: whether the request input was formatted for Responses Lite.

The `input_estimated_tokens` field uses Codex's existing `estimate_item_token_count` helper. Tool-schema and base-instruction estimates are intentionally labeled as coarse estimates; they are not intended to reproduce server tokenization exactly.

## Experimental interpretation

The first experiment should compare these events with the corresponding rollout `token_count` telemetry, especially `last_token_usage.input_tokens` / cached-input values.

The primary question is whether prompt growth is dominated by old retained tool outputs. A typical diagnostic sequence would compare:

```text
sequence | input_estimated_tokens | tool_output_tokens | old_tool_output_tokens | server input | server cached input
```

No pruning or mitigation should be added to this branch until the instrumentation has been validated against a controlled run.
