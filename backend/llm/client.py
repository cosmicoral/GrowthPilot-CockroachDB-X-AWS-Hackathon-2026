import asyncio
import json
import os

import boto3


class BedrockClient:
    """
    Asynchronous client wrapper for AWS Bedrock services.
    """

    def __init__(
        self,
        region_name: str | None = None,
        embedding_model: str | None = None,
        text_model: str | None = None,
    ):
        """
        Initialize the Bedrock client runtime using environment settings.

        Region and both model IDs are environment-driven so the deployed
        service can be pointed at a different Bedrock region without a
        code change. This matters because on-demand quota is granted
        per-region: the EU regions returned ThrottlingException on every
        request, so runtime inference is served from us-east-1.
        """
        self.region_name = region_name or os.getenv("AWS_REGION", "us-east-1")
        self.embedding_model = embedding_model or os.getenv(
            "BEDROCK_EMBEDDING_MODEL", "amazon.titan-embed-text-v2:0"
        )
        # Must be an inference-profile ID (the `us.` prefix), not a bare model
        # ID -- us-east-1 rejects bare Claude model IDs for on-demand calls.
        self.text_model = text_model or os.getenv(
            "BEDROCK_TEXT_MODEL", "us.anthropic.claude-sonnet-4-6"
        )
        self.client = boto3.client("bedrock-runtime", region_name=self.region_name)

    async def get_embedding(self, text: str) -> list[float]:
        """
        Generate a vector embedding for the given text using Amazon Titan.
        """
        body = json.dumps({
            "inputText": text,
            "dimensions": 1024,
            "normalize": True
        })

        response = await asyncio.to_thread(
            self.client.invoke_model,
            modelId=self.embedding_model,
            contentType="application/json",
            accept="application/json",
            body=body
        )

        response_body = json.loads(response["body"].read())
        return response_body["embedding"]

    async def generate_text(
        self,
        prompt: str,
        system_prompt: str | None = None,
        model_id: str | None = None,
        max_tokens: int = 2048,
        temperature: float = 0.7,
    ) -> str:
        """
        Generate text response/completion using Claude on AWS Bedrock.
        """
        messages = [{"role": "user", "content": [{"type": "text", "text": prompt}]}]

        payload = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": max_tokens,
            "messages": messages,
            "temperature": temperature,
        }

        if system_prompt:
            payload["system"] = system_prompt

        body = json.dumps(payload)

        response = await asyncio.to_thread(
            self.client.invoke_model,
            modelId=model_id or self.text_model,
            contentType="application/json",
            accept="application/json",
            body=body
        )

        response_body = json.loads(response["body"].read())
        return response_body["content"][0]["text"]

    async def generate_text_stream(
        self,
        prompt: str,
        system_prompt: str | None = None,
        model_id: str | None = None,
        max_tokens: int = 2048,
        temperature: float = 0.7,
    ):
        """
        Stream text response/completion using Claude on AWS Bedrock.

        Yields string chunks as they are generated.
        """
        messages = [{"role": "user", "content": [{"type": "text", "text": prompt}]}]

        payload = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": max_tokens,
            "messages": messages,
            "temperature": temperature,
        }

        if system_prompt:
            payload["system"] = system_prompt

        body = json.dumps(payload)

        response = await asyncio.to_thread(
            self.client.invoke_model_with_response_stream,
            modelId=model_id or self.text_model,
            contentType="application/json",
            accept="application/json",
            body=body,
        )

        _sentinel = object()

        stream = response.get("body")
        if stream:
            while True:
                # Use a sentinel instead of catching StopIteration, because
                # StopIteration raised inside asyncio.to_thread is converted
                # to RuntimeError in Python 3.11+.
                event = await asyncio.to_thread(
                    next, stream, _sentinel,
                )
                if event is _sentinel:
                    break

                chunk = event.get("chunk")
                if chunk:
                    chunk_obj = json.loads(chunk.get("bytes").decode())
                    if chunk_obj.get("type") == "content_block_delta":
                        yield chunk_obj["delta"]["text"]
