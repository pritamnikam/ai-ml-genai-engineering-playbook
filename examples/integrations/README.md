# Framework and model integrations

These are small, opt-in examples, separate from the offline concept notebooks.
Install only the extra for the integration you want to explore:

```powershell
python -m pip install -e ".[openai]"
python -m pip install -e ".[gemini]"
python -m pip install -e ".[anthropic]"
python -m pip install -e ".[aws]"
python -m pip install -e ".[langchain]"
python -m pip install -e ".[langgraph]"
python -m pip install -e ".[langsmith]"
python -m pip install -e ".[llamaindex]"
```

`model_providers.py` shows explicit calls for OpenAI, Gemini, Anthropic, Ollama,
Docker Model Runner, Bedrock Converse, and an **existing** SageMaker endpoint.
It does not provision cloud resources. Supply credentials and resource names
through environment variables; never place them in source files or notebooks.
Cloud APIs can incur charges.

The LangChain example uses a hosted model and requires `OPENAI_API_KEY`. The
LangGraph example is a deterministic approval workflow. The LangSmith example
uses the `LANGSMITH_TRACING`, `LANGSMITH_API_KEY`, and `LANGSMITH_PROJECT`
environment variables when tracing is desired. The LlamaIndex example uses
mock model components so its indexing and query wiring can be explored without
provider credentials.

All snippets are starting points, not application security controls. Add
timeouts, retries with limits, content validation, access controls, and
provider-specific data/privacy review before adapting them for a service.
