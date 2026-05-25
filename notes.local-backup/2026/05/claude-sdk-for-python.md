---
title: "Claude SDK for Python"
source: "https://github.com/anthropics/anthropic-sdk-python"
kind: "github"
captured_at: "2026-05-25T14:39:47.113936+00:00"
tags:
  - claude-api
  - python-sdk
  - anthropic
  - ai-infrastructure
  - api-client
---

# Claude SDK for Python

> Official Python SDK for accessing Anthropic's Claude API from Python applications, including messages, streaming, tools, cloud integrations, and beta agent/memory APIs.

## TL;DR

- `anthropics/anthropic-sdk-python` is the official Claude SDK for Python, published as the `anthropic` PyPI package.
- Install with `pip install anthropic`; requires Python 3.9+.
- Basic usage imports `Anthropic`, reads `ANTHROPIC_API_KEY` by default, and calls `client.messages.create(...)`.
- Example model in README: `claude-opus-4-6`; example call sets `max_tokens=1024` and sends a user message `"Hello, Claude"`.
- Repository metadata at capture: 3,515 stars, 690 forks, primary language Python, default branch `main`, MIT license.
- The repo includes support/examples for messages, streaming, text completions, structured outputs, tools, MCP, web search, thinking, images, batch results, memory, agents, Bedrock, Vertex, Azure, and workload identity.
- Full documentation is hosted at `platform.claude.com/docs/en/api/sdks/python`.

## Key claims & findings

- README title: `Claude SDK for Python`.
- Package badge links to PyPI project: `https://pypi.org/project/anthropic/`.
- Core claim: “The Claude SDK for Python provides access to the Claude API from Python applications.”
- Documentation URL: `https://platform.claude.com/docs/en/api/sdks/python`.
- Installation command:
  ```sh
  pip install anthropic
  ```
- Minimum runtime requirement: `Python 3.9+`.
- Basic client pattern:
  ```python
  import os
  from anthropic import Anthropic

  client = Anthropic(
      api_key=os.environ.get("ANTHROPIC_API_KEY"),  # This is the default and can be omitted
  )
  ```
- Basic Messages API call pattern:
  ```python
  message = client.messages.create(
      max_tokens=1024,
      messages=[
          {
              "role": "user",
              "content": "Hello, Claude",
          }
      ],
      model="claude-opus-4-6",
  )
  print(message.content)
  ```
- Authentication default: `ANTHROPIC_API_KEY` environment variable; explicit `api_key=os.environ.get("ANTHROPIC_API_KEY")` “is the default and can be omitted.”
- License: MIT; README says “See the LICENSE file for details.”
- Contributing instructions are in `CONTRIBUTING.md`.
- Top-level API/client implementation files include:
  - `src/anthropic/_client.py`
  - `src/anthropic/_base_client.py`
  - `src/anthropic/_streaming.py`
  - `src/anthropic/_exceptions.py`
  - `src/anthropic/_models.py`
  - `src/anthropic/pagination.py`
  - `src/anthropic/py.typed`
- Main stable resource areas visible in source tree:
  - `src/anthropic/resources/messages/messages.py`
  - `src/anthropic/resources/messages/batches.py`
  - `src/anthropic/resources/completions.py`
  - `src/anthropic/resources/models.py`
- Beta resource areas visible in source tree:
  - `src/anthropic/resources/beta/agents`
  - `src/anthropic/resources/beta/environments`
  - `src/anthropic/resources/beta/files.py`
  - `src/anthropic/resources/beta/memory_stores`
  - `src/anthropic/resources/beta/messages`
  - `src/anthropic/resources/beta/models.py`
  - `src/anthropic/resources/beta/sessions`
  - `src/anthropic/resources/beta/skills`
  - `src/anthropic/resources/beta/user_profiles.py`
  - `src/anthropic/resources/beta/vaults`
  - `src/anthropic/resources/beta/webhooks.py`
- Cloud/provider integrations appear under:
  - `src/anthropic/lib/bedrock`
  - `src/anthropic/lib/vertex`
  - `src/anthropic/lib/aws`
  - examples: `examples/bedrock.py`, `examples/vertex.py`, `examples/azure.py`, `examples/workload_identity.py`
- Tooling/library support appears under:
  - `src/anthropic/lib/tools`
  - `src/anthropic/tools/memory.py`
  - `src/anthropic/lib/tools/mcp.py`
  - `src/anthropic/lib/tools/agent_toolset.py`
  - `src/anthropic/lib/tools/_beta_runner.py`
  - `src/anthropic/lib/tools/_beta_session_runner.py`
  - `src/anthropic/lib/tools/_skills.py`
- Streaming support appears under:
  - `src/anthropic/lib/streaming/_messages.py`
  - `src/anthropic/lib/streaming/_beta_messages.py`
  - examples: `messages_stream.py`, `thinking_stream.py`, `tools_stream.py`, `web_search_stream.py`, `structured_outputs_streaming.py`
- Example files indicate practical coverage for:
  - `agents.py`, `agents_comprehensive.py`, `agents_with_files.py`
  - `managed-agents-observe-tool-calls.py`
  - `managed-agents-private-sandbox-worker.py`
  - `managed-agents-worker-dispatch.py`
  - `mcp_tool_runner.py`
  - `memory/basic.py`
  - `structured_outputs.py`
  - `thinking.py`
  - `tools.py`, `tools_runner.py`, `tools_runner_search_tool.py`
  - `web_search.py`
  - `images.py`
  - `batch_results.py`
- Automation/workflows present:
  - `.github/workflows/ci.yml`
  - `.github/workflows/create-releases.yml`
  - `.github/workflows/detect-breaking-changes.yml`
  - `.github/workflows/publish-pypi.yml`
  - `.github/workflows/claude.yml`

## Entities & links

- [[Claude SDK for Python]]
- [[Claude API]]
- [[Anthropic]]
- [[Anthropic Python SDK]]
- [[anthropic]]
- [[PyPI]]
- [[ANTHROPIC_API_KEY]]
- [[Anthropic]]
- [[client.messages.create]]
- [[Messages API]]
- [[claude-opus-4-6]]
- [[Python 3.9+]]
- [[MIT License]]
- [[Bedrock]]
- [[Vertex]]
- [[Azure]]
- [[workload identity]]
- [[MCP]]
- [[web search]]
- [[structured outputs]]
- [[thinking]]
- [[tools]]
- [[agents]]
- [[memory stores]]
- [[sessions]]
- [[skills]]
- [[vaults]]
- [[webhooks]]
- [[Stainless]]

## Open questions

- Which SDK version was current at capture time is not stated in the provided README excerpt, only the PyPI badge is shown.
- The repo description and topics are empty despite the project being the official Claude Python SDK.
- The source tree exposes many beta APIs, but the README does not explain stability guarantees or migration paths for beta features.
- The README example uses `claude-opus-4-6`; the source does not state model availability, pricing, regional constraints, or deprecation policy.
- The differences among direct Anthropic API usage, Bedrock, Vertex, Azure, and workload identity examples are not described in the README excerpt.
- The repository includes legacy text completions examples, but the README centers the Messages API; current guidance on when to use completions is not included.
- The source tree references managed agents, environments, sessions, memory stores, skills, vaults, and webhooks, but the provided content does not explain their API semantics.

## Source

https://github.com/anthropics/anthropic-sdk-python