"""Opt-in model calls; install the matching extra and provide credentials."""

import json
import os
from urllib.request import Request, urlopen


def ask_openai(prompt: str) -> str:
    from openai import OpenAI

    response = OpenAI().responses.create(
        model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
        input=prompt,
    )
    return response.output_text


def ask_gemini(prompt: str) -> str:
    from google import genai

    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    response = client.models.generate_content(
        model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
        contents=prompt,
    )
    if response.text is None:
        raise RuntimeError("Gemini returned no text")
    return response.text


def ask_anthropic(prompt: str) -> str:
    import anthropic

    response = anthropic.Anthropic().messages.create(
        model=os.getenv("ANTHROPIC_MODEL", "claude-3-5-haiku-latest"),
        max_tokens=500,
        messages=[{"role": "user", "content": prompt}],
    )
    if not response.content or not hasattr(response.content[0], "text"):
        raise RuntimeError("Anthropic returned no text block")
    return response.content[0].text


def ask_ollama(prompt: str) -> str:
    endpoint = os.getenv("OLLAMA_URL", "http://localhost:11434")
    model = os.getenv("OLLAMA_MODEL")
    if not model:
        raise RuntimeError("Set OLLAMA_MODEL to a model available in Ollama")
    body = json.dumps(
        {"model": model, "messages": [{"role": "user", "content": prompt}], "stream": False}
    ).encode("utf-8")
    request = Request(
        f"{endpoint.rstrip('/')}/api/chat",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urlopen(request, timeout=30) as response:
        result = json.load(response)
    return result["message"]["content"]


def ask_docker_model_runner(prompt: str) -> str:
    from openai import OpenAI

    client = OpenAI(
        base_url=os.getenv(
            "DOCKER_MODEL_RUNNER_URL", "http://localhost:12434/engines/v1"
        ),
        api_key="not-needed-for-local-model-runner",
    )
    model = os.getenv("DOCKER_MODEL_RUNNER_MODEL")
    if not model:
        raise RuntimeError("Set DOCKER_MODEL_RUNNER_MODEL to an available local model")
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
    )
    content = response.choices[0].message.content
    if content is None:
        raise RuntimeError("Docker Model Runner returned no text")
    return content


def ask_bedrock(prompt: str) -> str:
    import boto3

    model_id = os.getenv("BEDROCK_MODEL_ID")
    if not model_id:
        raise RuntimeError("Set BEDROCK_MODEL_ID to an enabled Bedrock model")
    response = boto3.client(
        "bedrock-runtime", region_name=os.getenv("AWS_DEFAULT_REGION")
    ).converse(
        modelId=model_id,
        messages=[{"role": "user", "content": [{"text": prompt}]}],
    )
    blocks = response["output"]["message"]["content"]
    text = [block["text"] for block in blocks if "text" in block]
    if not text:
        raise RuntimeError("Bedrock returned no text block")
    return "\n".join(text)


def invoke_sagemaker(prompt: str) -> dict[str, object]:
    """Invoke an existing endpoint; this function does not provision resources."""
    import boto3

    endpoint_name = os.getenv("SAGEMAKER_ENDPOINT_NAME")
    if not endpoint_name:
        raise RuntimeError("Set SAGEMAKER_ENDPOINT_NAME to an existing endpoint")
    response = boto3.client(
        "sagemaker-runtime", region_name=os.getenv("AWS_DEFAULT_REGION")
    ).invoke_endpoint(
        EndpointName=endpoint_name,
        ContentType="application/json",
        Body=json.dumps({"inputs": prompt}).encode("utf-8"),
    )
    return json.loads(response["Body"].read())
