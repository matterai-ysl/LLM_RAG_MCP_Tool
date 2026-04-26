# Materials Science Intelligent Q&A MCP Server

English-only MCP server for materials science questions with RAG retrieval and LLM fallback. Returns JSON format with both answers for AI agent decision-making.

## Key Features

🔬 **Materials Science Focused**: Optimized specifically for materials science questions
🔍 **RAG Retrieval**: Academic literature retrieval based on OpenScholar platform  
🤖 **LLM Fallback**: General AI answers via LiteLLM
📚 **Academic Citations**: Automatic extraction and formatting of references
🚀 **High Concurrency**: Support for up to 5 concurrent sessions
🔄 **Auto Retry**: Up to 3 retry attempts with exponential backoff
⚡ **Async Architecture**: Fully asynchronous for optimal performance
📄 **JSON Output**: Structured response for AI agent processing

## Critical AI Agent Instructions

### Input Processing Requirements
⚠️ **English Only**: This tool ONLY accepts English input
🚫 **No History**: NO conversation history is maintained between requests  
🔧 **Question Refinement**: EXTRACT and REFINE user questions from conversation history
🎯 **Precise Input**: Input should be well-formulated, specific questions
❌ **No Direct Forwarding**: DO NOT directly forward vague user queries

### Output Synthesis Requirements  
🤖 **Dual Answer Processing**: Tool returns BOTH RAG and LLM answers
📚 **Prioritize RAG**: Use RAG (academic) as primary when available
🔗 **Intelligent Synthesis**: Combine both answers into comprehensive response
📖 **Citation Integration**: Include proper citations from RAG references
🏷️ **Source Attribution**: Always indicate sources in final response

## Installation & Setup

### 1. Environment Preparation With uv

This project uses `uv` for dependency management. `pyproject.toml` and
`uv.lock` are the source of truth for the Python environment.

Ensure Python 3.10+ and `uv` are available, then install the locked
environment and Playwright Chromium runtime:

```bash
cd MCP_LLM_RAG_Tool
uv sync
uv run python -m playwright install chromium
```

For the detailed runtime requirements and verified local package versions,
see [REQUIREMENTS.md](REQUIREMENTS.md).

### 2. Environment Variables

Create a local `.env` file with the API configuration. This file is ignored by
Git and should not be committed.

```env
BASE_URL=https://vip.dmxapi.com/v1
OPENAI_API_KEY=your-api-key-here
```

## MCP Startup

The entry point is `materials_science_qa_mcp.py`. The default transport is
`streamable-http`, so the explicit and default commands below are equivalent:

### Streamable HTTP

```bash
uv run python materials_science_qa_mcp.py streamable-http
```

The MCP server listens on port `8110`.

### STDIO

```bash
uv run python materials_science_qa_mcp.py stdio
```

### SSE

```bash
uv run python materials_science_qa_mcp.py sse
```

### STDIO Client Configuration

Use this form for MCP clients that launch the server process directly:

```json
{
  "mcpServers": {
    "materials-science-rag-en": {
      "command": "uv",
      "args": [
        "--directory",
        "/absolute/path/to/MCP_LLM_RAG_Tool",
        "run",
        "python",
        "materials_science_qa_mcp.py",
        "stdio"
      ],
      "env": {
        "BASE_URL": "https://vip.dmxapi.com/v1",
        "OPENAI_API_KEY": "your-api-key-here"
      }
    }
  }
}
```

## Available Tools

### 1. answer_materials_science_question

Answers materials science questions with both RAG and LLM approaches.

**Parameters:**
- `question` (string): Materials science question in English

**Example Input:**
```
How to synthesize lithium-rich disordered cathode materials?
```

**JSON Response Structure:**
```json
{
  "question": "How to synthesize lithium-rich disordered cathode materials?",
  "rag_retrieval": {
    "success": true,
    "answer": "Detailed academic answer...",
    "references": ["Author et al. Paper Title. Journal. Year.", "..."],
    "source": "OpenScholar",
    "timestamp": "2023-09-06T12:00:00Z"
  },
  "llm_answer": {
    "success": true,
    "answer": "General AI answer...",
    "source": "LiteLLM (GPT-3.5-turbo)",
    "timestamp": "2023-09-06T12:00:00Z"
  },
  "processing_info": {
    "concurrent_sessions_used": 1,
    "max_concurrent_limit": 5,
    "max_retries": 3,
    "timeout_seconds": 180,
    "timestamp": "2023-09-06T12:00:00Z"
  }
}
```

### 2. get_system_status

Returns system status information in JSON format.

**JSON Response Structure:**
```json
{
  "system_name": "Materials Science MCP Server",
  "services": {
    "openscholar_rag": {
      "status": "online|offline|error",
      "error": null,
      "description": "Academic literature retrieval from OpenScholar"
    },
    "litellm_fallback": {
      "status": "online|offline|error", 
      "error": null,
      "description": "General AI answer using LiteLLM"
    }
  },
  "configuration": {
    "max_concurrent_sessions": 5,
    "current_active_sessions": 1,
    "timeout_seconds": 180,
    "max_retries": 3
  },
  "capabilities": [...],
  "limitations": [...],
  "timestamp": "2023-09-06T12:00:00Z"
}
```

## Enhanced AI Agent Processing Workflow

### 1. Pre-Processing (Question Refinement)

```python
# AI Agent should refine vague user queries before calling tool
user_query = "Tell me about batteries"
refined_question = "What are the fundamental principles of lithium-ion battery operation and key material requirements?"

# Call tool with refined question
response = await answer_materials_science_question(refined_question)
```

### 2. Response Synthesis Logic

```python
# Comprehensive processing of dual answers
response_data = json.loads(tool_response)
rag_result = response_data['rag_retrieval']
llm_result = response_data['llm_answer']

if rag_result['success']:
    # Primary strategy: RAG + LLM synthesis
    primary_content = rag_result['answer']
    references = rag_result['references']
    
    # Add LLM insights to fill gaps
    if llm_result['success']:
        supplementary_content = llm_result['answer']
        # Intelligently merge both sources
    
    # Format with proper citations
    final_response = f"{primary_content}\n\nReferences:\n"
    for i, ref in enumerate(references, 1):
        final_response += f"[{i}] {ref}\n"
    
elif llm_result['success']:
    # Fallback strategy: LLM only with clear attribution
    final_response = f"{llm_result['answer']}\n\n*Note: Based on general AI knowledge (academic retrieval unavailable)*"
    
else:
    # Error handling with helpful guidance
    final_response = "Both systems currently unavailable. Please retry or refine your question."
```

### 3. Enhanced Response Guidelines

- **Question Refinement**: Always extract and refine vague user queries
- **Intelligent Synthesis**: Combine RAG and LLM answers meaningfully  
- **Proper Citations**: Format references as [1], [2] with full list at end
- **Source Transparency**: Always indicate which sources were used
- **LLM Focus**: Focused answers only, no fabricated references
- **Error Handling**: Provide constructive guidance when systems fail

## System Architecture

```
English Question
    ↓
MCP Tool Interface
    ↓
Concurrent Control (Semaphore)
    ↓
┌─────────────────┐    ┌─────────────────┐
│   RAG Retrieval │    │   LLM Answer    │
│ (OpenScholar)   │    │  (LiteLLM)      │
└─────────────────┘    └─────────────────┘
    ↓                         ↓
Academic Answer            General AI Answer
+ References              
    ↓                         ↓
        JSON Response
        (Both Answers)
            ↓
    AI Agent Processes
            ↓
    User Gets Best Answer
```

## Configuration Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| MAX_RETRIES | Maximum retry attempts | 1 |
| TIMEOUT_SECONDS | Request timeout | 60 |
| CONCURRENT_LIMIT | Max concurrent sessions | 10 |
| MCP port | Streamable HTTP/SSE server port | 8110 |

## Supported Question Types

The system supports a wide range of materials science topics:
- Material synthesis methods
- Material property analysis  
- Battery material research
- Nanomaterial applications
- Material characterization techniques
- Solid-state physics
- Chemical engineering processes

## Example Questions

**Good Examples** (precise, well-formulated):
- "How to synthesize lithium-rich disordered cathode materials using solid-state methods?"
- "What are the advantages of solid-state electrolytes over liquid electrolytes in lithium-ion batteries?"
- "Explain the mechanism of lithium dendrite formation in battery anodes."

**Poor Examples** (too vague or non-English):
- "Tell me about batteries" (too vague)
- "如何合成材料?" (not English)
- "What's up with materials?" (imprecise)

## Troubleshooting

### Q: Why do I get both RAG and LLM answers?

A: The tool provides both so the AI agent can choose the best response based on quality, relevance, and availability.

### Q: What if RAG retrieval often fails?

A: The system has built-in retry mechanisms and will automatically provide LLM fallback answers.

### Q: How to improve concurrent processing?

A: Adjust `CONCURRENT_LIMIT` parameter, but consider:
- Server resource limits
- OpenScholar rate limiting
- Performance impact

### Q: Can I use this for non-materials science questions?

A: While possible, the system is optimized for materials science and may not perform well on other topics.

## Technical Requirements

- Python 3.10+
- uv
- Internet connection for OpenScholar and LiteLLM
- Valid OpenAI API key
- Playwright Chromium runtime
- Sufficient system resources for browser automation

## License

This project uses the MIT License.
