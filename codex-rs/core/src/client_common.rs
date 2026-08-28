pub use codex_api::ResponseEvent;
use codex_protocol::error::Result;
use codex_protocol::models::BaseInstructions;
use codex_protocol::models::ContentItem;
use codex_protocol::models::FunctionCallOutputContentItem;
use codex_protocol::models::ResponseItem;
use codex_tools::ToolSpec;
use futures::Stream;
use serde_json::Value;
use std::pin::Pin;
use std::sync::Arc;
use std::sync::atomic::AtomicU64;
use std::sync::atomic::Ordering;
use std::task::Context;
use std::task::Poll;
use tokio::sync::mpsc;
use tokio_util::sync::CancellationToken;

const CONTEXT_USAGE_TRACE_TARGET: &str = "codex_core::context_usage_experiment";
const RECENT_TOOL_OUTPUT_COUNT: usize = 4;
static CONTEXT_USAGE_REQUEST_SEQUENCE: AtomicU64 = AtomicU64::new(0);

/// API request payload for a single model turn
#[derive(Debug, Clone)]
pub struct Prompt {
    /// Conversation context input items.
    pub input: Vec<ResponseItem>,

    /// Tools available to the model, including additional tools sourced from
    /// external MCP servers.
    pub(crate) tools: Arc<[ToolSpec]>,

    /// Whether parallel tool calls are permitted for this prompt.
    pub(crate) parallel_tool_calls: bool,

    pub base_instructions: BaseInstructions,

    /// Optional the output schema for the model's response.
    pub output_schema: Option<Value>,

    /// Whether the Responses API should strictly validate `output_schema`.
    pub output_schema_strict: bool,

    pub(crate) cyber_access_program: Option<codex_protocol::turn_input::CyberAccessProgram>,
}

impl Default for Prompt {
    fn default() -> Self {
        Self {
            input: Vec::new(),
            tools: Arc::default(),
            parallel_tool_calls: false,
            base_instructions: BaseInstructions::default(),
            output_schema: None,
            output_schema_strict: true,
            cyber_access_program: None,
        }
    }
}

impl Prompt {
    pub(crate) fn get_formatted_input_for_request(
        &self,
        use_responses_lite: bool,
    ) -> Vec<ResponseItem> {
        let mut input = self.input.clone();
        if use_responses_lite {
            strip_image_details(&mut input);
        }
        record_context_usage_experiment(self, &input, use_responses_lite);
        input
    }
}

#[derive(Default)]
struct ContextUsageBreakdown {
    input_estimated_tokens: i64,
    user_message_tokens: i64,
    developer_message_tokens: i64,
    assistant_message_tokens: i64,
    other_message_tokens: i64,
    reasoning_tokens: i64,
    tool_call_tokens: i64,
    tool_output_tokens: i64,
    recent_tool_output_tokens: i64,
    largest_tool_output_tokens: i64,
    compaction_tokens: i64,
    agent_message_tokens: i64,
    additional_tools_tokens: i64,
    other_tokens: i64,
    tool_output_count: usize,
}

impl ContextUsageBreakdown {
    fn old_tool_output_tokens(&self) -> i64 {
        self.tool_output_tokens
            .saturating_sub(self.recent_tool_output_tokens)
    }
}

fn estimate_prompt_input_breakdown(input: &[ResponseItem]) -> ContextUsageBreakdown {
    let mut breakdown = ContextUsageBreakdown::default();
    let mut tool_outputs = Vec::new();

    for item in input {
        let tokens = crate::context_manager::estimate_item_token_count(item);
        breakdown.input_estimated_tokens = breakdown.input_estimated_tokens.saturating_add(tokens);

        match item {
            ResponseItem::Message { role, .. } => match role.as_str() {
                "user" => {
                    breakdown.user_message_tokens =
                        breakdown.user_message_tokens.saturating_add(tokens);
                }
                "developer" => {
                    breakdown.developer_message_tokens =
                        breakdown.developer_message_tokens.saturating_add(tokens);
                }
                "assistant" => {
                    breakdown.assistant_message_tokens =
                        breakdown.assistant_message_tokens.saturating_add(tokens);
                }
                _ => {
                    breakdown.other_message_tokens =
                        breakdown.other_message_tokens.saturating_add(tokens);
                }
            },
            ResponseItem::Reasoning { .. } => {
                breakdown.reasoning_tokens = breakdown.reasoning_tokens.saturating_add(tokens);
            }
            ResponseItem::FunctionCall { .. }
            | ResponseItem::ToolSearchCall { .. }
            | ResponseItem::WebSearchCall { .. }
            | ResponseItem::ImageGenerationCall { .. }
            | ResponseItem::CustomToolCall { .. }
            | ResponseItem::LocalShellCall { .. } => {
                breakdown.tool_call_tokens = breakdown.tool_call_tokens.saturating_add(tokens);
            }
            ResponseItem::FunctionCallOutput { .. }
            | ResponseItem::ToolSearchOutput { .. }
            | ResponseItem::CustomToolCallOutput { .. } => {
                breakdown.tool_output_tokens = breakdown.tool_output_tokens.saturating_add(tokens);
                breakdown.largest_tool_output_tokens =
                    breakdown.largest_tool_output_tokens.max(tokens);
                breakdown.tool_output_count = breakdown.tool_output_count.saturating_add(1);
                tool_outputs.push(tokens);
            }
            ResponseItem::Compaction { .. }
            | ResponseItem::CompactionTrigger { .. }
            | ResponseItem::ContextCompaction { .. } => {
                breakdown.compaction_tokens = breakdown.compaction_tokens.saturating_add(tokens);
            }
            ResponseItem::AgentMessage { .. } => {
                breakdown.agent_message_tokens =
                    breakdown.agent_message_tokens.saturating_add(tokens);
            }
            ResponseItem::AdditionalTools { .. } => {
                breakdown.additional_tools_tokens =
                    breakdown.additional_tools_tokens.saturating_add(tokens);
            }
            ResponseItem::Other => {
                breakdown.other_tokens = breakdown.other_tokens.saturating_add(tokens);
            }
        }
    }

    breakdown.recent_tool_output_tokens = tool_outputs
        .iter()
        .rev()
        .take(RECENT_TOOL_OUTPUT_COUNT)
        .copied()
        .fold(0i64, i64::saturating_add);

    breakdown
}

fn approx_tokens_from_bytes(bytes: usize) -> usize {
    bytes.saturating_add(3) / 4
}

fn record_context_usage_experiment(
    prompt: &Prompt,
    formatted_input: &[ResponseItem],
    use_responses_lite: bool,
) {
    let sequence = CONTEXT_USAGE_REQUEST_SEQUENCE.fetch_add(1, Ordering::Relaxed) + 1;
    let breakdown = estimate_prompt_input_breakdown(formatted_input);
    let tool_schema_bytes = serde_json::to_vec(prompt.tools.as_ref())
        .map(|json| json.len())
        .unwrap_or_default();
    let base_instruction_bytes = prompt.base_instructions.text.len();

    tracing::info!(
        target: CONTEXT_USAGE_TRACE_TARGET,
        sequence,
        use_responses_lite,
        input_items = formatted_input.len(),
        input_estimated_tokens = breakdown.input_estimated_tokens,
        user_message_tokens = breakdown.user_message_tokens,
        developer_message_tokens = breakdown.developer_message_tokens,
        assistant_message_tokens = breakdown.assistant_message_tokens,
        other_message_tokens = breakdown.other_message_tokens,
        reasoning_tokens = breakdown.reasoning_tokens,
        tool_call_tokens = breakdown.tool_call_tokens,
        tool_output_count = breakdown.tool_output_count,
        tool_output_tokens = breakdown.tool_output_tokens,
        recent_tool_output_tokens = breakdown.recent_tool_output_tokens,
        old_tool_output_tokens = breakdown.old_tool_output_tokens(),
        largest_tool_output_tokens = breakdown.largest_tool_output_tokens,
        compaction_tokens = breakdown.compaction_tokens,
        agent_message_tokens = breakdown.agent_message_tokens,
        additional_tools_tokens = breakdown.additional_tools_tokens,
        other_tokens = breakdown.other_tokens,
        tool_count = prompt.tools.len(),
        tool_schema_bytes,
        tool_schema_estimated_tokens = approx_tokens_from_bytes(tool_schema_bytes),
        base_instruction_bytes,
        base_instruction_estimated_tokens = approx_tokens_from_bytes(base_instruction_bytes),
        "context usage experiment prompt"
    );
}

fn strip_image_details(items: &mut [ResponseItem]) {
    for item in items {
        match item {
            ResponseItem::Message { content, .. } => {
                for content_item in content {
                    if let ContentItem::InputImage { detail, .. } = content_item {
                        *detail = None;
                    }
                }
            }
            ResponseItem::FunctionCallOutput { output, .. }
            | ResponseItem::CustomToolCallOutput { output, .. } => {
                if let Some(content) = output.content_items_mut() {
                    for content_item in content {
                        if let FunctionCallOutputContentItem::InputImage { detail, .. } =
                            content_item
                        {
                            *detail = None;
                        }
                    }
                }
            }
            ResponseItem::AdditionalTools { .. }
            | ResponseItem::Reasoning { .. }
            | ResponseItem::AgentMessage { .. }
            | ResponseItem::LocalShellCall { .. }
            | ResponseItem::FunctionCall { .. }
            | ResponseItem::ToolSearchCall { .. }
            | ResponseItem::CustomToolCall { .. }
            | ResponseItem::ToolSearchOutput { .. }
            | ResponseItem::WebSearchCall { .. }
            | ResponseItem::ImageGenerationCall { .. }
            | ResponseItem::Compaction { .. }
            | ResponseItem::CompactionTrigger { .. }
            | ResponseItem::ContextCompaction { .. }
            | ResponseItem::Other => {}
        }
    }
}

pub struct ResponseStream {
    pub(crate) rx_event: mpsc::Receiver<Result<ResponseEvent>>,
    /// Signals the mapper task that the consumer stopped polling before the
    /// provider stream reached its own terminal event.
    pub(crate) consumer_dropped: CancellationToken,
}

impl Stream for ResponseStream {
    type Item = Result<ResponseEvent>;

    fn poll_next(mut self: Pin<&mut Self>, cx: &mut Context<'_>) -> Poll<Option<Self::Item>> {
        self.rx_event.poll_recv(cx)
    }
}

impl Drop for ResponseStream {
    fn drop(&mut self) {
        self.consumer_dropped.cancel();
    }
}

#[cfg(test)]
#[path = "client_common_tests.rs"]
mod tests;
