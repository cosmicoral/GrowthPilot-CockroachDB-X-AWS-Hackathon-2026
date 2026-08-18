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

    @staticmethod
    def _is_nova(model_id: str) -> bool:
        """Amazon Nova models use a different request/response shape."""
        return "amazon.nova" in model_id

    @staticmethod
    def _nova_payload(
        prompt: str,
        system_prompt: str | None,
        max_tokens: int,
        temperature: float,
    ) -> dict:
        """Build an Amazon Nova InvokeModel body.

        Nova does not accept the Anthropic `messages` schema: content parts
        are `{"text": ...}` rather than `{"type": "text", "text": ...}`,
        generation settings live under `inferenceConfig`, and `system` is a
        list of content blocks rather than a bare string.
        """
        payload: dict = {
            "messages": [
                {"role": "user", "content": [{"text": prompt}]},
            ],
            "inferenceConfig": {
                "maxTokens": max_tokens,
                "temperature": temperature,
            },
        }

        if system_prompt:
            payload["system"] = [{"text": system_prompt}]

        return payload

    async def generate_text(
        self,
        prompt: str,
        system_prompt: str | None = None,
        model_id: str | None = None,
        max_tokens: int = 2048,
        temperature: float = 0.7,
    ) -> str:
        """
        Generate a text completion on AWS Bedrock.

        Anthropic models are the primary path. Amazon Nova is supported as a
        fallback because Anthropic model access on Bedrock is gated behind a
        per-provider use-case form: if that approval has not landed, every
        Anthropic model ID fails with ResourceNotFoundException and no amount
        of switching between Claude versions helps. Nova needs no such form,
        so pointing BEDROCK_TEXT_MODEL at e.g. `amazon.nova-lite-v1:0`
        restores text generation with a config change rather than a redeploy.
        """
        resolved_model = model_id or self.text_model

        if self._is_nova(resolved_model):
            payload = self._nova_payload(
                prompt, system_prompt, max_tokens, temperature,
            )
        else:
            payload = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": max_tokens,
                "messages": [
                    {"role": "user", "content": [{"type": "text", "text": prompt}]},
                ],
                "temperature": temperature,
            }

            if system_prompt:
                payload["system"] = system_prompt

        response = await asyncio.to_thread(
            self.client.invoke_model,
            modelId=resolved_model,
            contentType="application/json",
            accept="application/json",
            body=json.dumps(payload),
        )

        response_body = json.loads(response["body"].read())

        if self._is_nova(resolved_model):
            return response_body["output"]["message"]["content"][0]["text"]

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
        Stream a text completion on AWS Bedrock.

        Yields string chunks as they are generated. Handles both the Anthropic
        and Amazon Nova stream shapes -- see generate_text for why Nova is
        supported at all.
        """
        resolved_model = model_id or self.text_model

        if self._is_nova(resolved_model):
            payload = self._nova_payload(
                prompt, system_prompt, max_tokens, temperature,
            )
        else:
            payload = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": max_tokens,
                "messages": [
                    {"role": "user", "content": [{"type": "text", "text": prompt}]},
                ],
                "temperature": temperature,
            }

            if system_prompt:
                payload["system"] = system_prompt

        response = await asyncio.to_thread(
            self.client.invoke_model_with_response_stream,
            modelId=resolved_model,
            contentType="application/json",
            accept="application/json",
            body=json.dumps(payload),
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
                if not chunk:
                    continue

                chunk_obj = json.loads(chunk.get("bytes").decode())

                if self._is_nova(resolved_model):
                    # Nova streams {"contentBlockDelta": {"delta": {"text": ...}}}
                    # instead of Anthropic's typed content_block_delta events.
                    delta = (
                        chunk_obj.get("contentBlockDelta", {})
                        .get("delta", {})
                        .get("text")
                    )
                    if delta:
                        yield delta
                elif chunk_obj.get("type") == "content_block_delta":
                    yield chunk_obj["delta"]["text"]
