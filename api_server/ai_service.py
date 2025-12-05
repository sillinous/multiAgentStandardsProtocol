"""
AI Service Layer
================

Provider-agnostic AI service that abstracts different LLM providers
(OpenAI, Anthropic, Azure, Google, Local) behind a common interface.
"""

import asyncio
import hashlib
import json
import os
import time
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
import uuid

import httpx


# ============================================================================
# Provider Abstractions
# ============================================================================

class AIProviderBase(ABC):
    """Abstract base class for AI providers"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.api_key = config.get("api_key")
        self.base_url = config.get("base_url")
        self.default_model = config.get("default_model")
        self.timeout = config.get("timeout", 120)

    @abstractmethod
    async def complete(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate a completion from the model"""
        pass

    @abstractmethod
    async def embed(
        self,
        texts: List[str],
        model: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate embeddings for texts"""
        pass

    @abstractmethod
    def estimate_tokens(self, text: str) -> int:
        """Estimate token count for text"""
        pass

    @abstractmethod
    def get_available_models(self) -> List[Dict[str, Any]]:
        """Get list of available models"""
        pass


class OpenAIProvider(AIProviderBase):
    """OpenAI API provider"""

    DEFAULT_BASE_URL = "https://api.openai.com/v1"

    MODELS = {
        "gpt-4o": {"context": 128000, "cost_input": 0.005, "cost_output": 0.015},
        "gpt-4o-mini": {"context": 128000, "cost_input": 0.00015, "cost_output": 0.0006},
        "gpt-4-turbo": {"context": 128000, "cost_input": 0.01, "cost_output": 0.03},
        "gpt-4": {"context": 8192, "cost_input": 0.03, "cost_output": 0.06},
        "gpt-3.5-turbo": {"context": 16385, "cost_input": 0.0005, "cost_output": 0.0015},
        "text-embedding-3-large": {"context": 8191, "cost_input": 0.00013, "cost_output": 0},
        "text-embedding-3-small": {"context": 8191, "cost_input": 0.00002, "cost_output": 0},
    }

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.base_url = config.get("base_url", self.DEFAULT_BASE_URL)
        self.default_model = config.get("default_model", "gpt-4o-mini")

    async def complete(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs
    ) -> Dict[str, Any]:
        model = model or self.default_model

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            start_time = time.time()

            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    **kwargs
                }
            )

            latency_ms = int((time.time() - start_time) * 1000)

            if response.status_code != 200:
                return {
                    "success": False,
                    "error_code": str(response.status_code),
                    "error_message": response.text,
                    "latency_ms": latency_ms
                }

            data = response.json()
            usage = data.get("usage", {})

            model_info = self.MODELS.get(model, {"cost_input": 0, "cost_output": 0})
            input_cost = (usage.get("prompt_tokens", 0) / 1000) * model_info["cost_input"]
            output_cost = (usage.get("completion_tokens", 0) / 1000) * model_info["cost_output"]

            return {
                "success": True,
                "content": data["choices"][0]["message"]["content"],
                "model": model,
                "input_tokens": usage.get("prompt_tokens", 0),
                "output_tokens": usage.get("completion_tokens", 0),
                "total_tokens": usage.get("total_tokens", 0),
                "estimated_cost": input_cost + output_cost,
                "finish_reason": data["choices"][0].get("finish_reason"),
                "latency_ms": latency_ms,
                "provider": "openai"
            }

    async def embed(
        self,
        texts: List[str],
        model: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        model = model or "text-embedding-3-small"

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            start_time = time.time()

            response = await client.post(
                f"{self.base_url}/embeddings",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": model,
                    "input": texts,
                    **kwargs
                }
            )

            latency_ms = int((time.time() - start_time) * 1000)

            if response.status_code != 200:
                return {
                    "success": False,
                    "error_code": str(response.status_code),
                    "error_message": response.text,
                    "latency_ms": latency_ms
                }

            data = response.json()
            usage = data.get("usage", {})

            return {
                "success": True,
                "embeddings": [item["embedding"] for item in data["data"]],
                "model": model,
                "total_tokens": usage.get("total_tokens", 0),
                "latency_ms": latency_ms,
                "provider": "openai"
            }

    def estimate_tokens(self, text: str) -> int:
        # Rough approximation: ~4 chars per token for English
        return len(text) // 4

    def get_available_models(self) -> List[Dict[str, Any]]:
        return [
            {
                "model_name": name,
                "context_window": info["context"],
                "cost_per_1k_input": info["cost_input"],
                "cost_per_1k_output": info["cost_output"],
                "capabilities": ["chat"] if "gpt" in name else ["embedding"]
            }
            for name, info in self.MODELS.items()
        ]


class AnthropicProvider(AIProviderBase):
    """Anthropic Claude API provider"""

    DEFAULT_BASE_URL = "https://api.anthropic.com/v1"

    MODELS = {
        "claude-3-5-sonnet-20241022": {"context": 200000, "cost_input": 0.003, "cost_output": 0.015},
        "claude-3-5-haiku-20241022": {"context": 200000, "cost_input": 0.001, "cost_output": 0.005},
        "claude-3-opus-20240229": {"context": 200000, "cost_input": 0.015, "cost_output": 0.075},
        "claude-3-sonnet-20240229": {"context": 200000, "cost_input": 0.003, "cost_output": 0.015},
        "claude-3-haiku-20240307": {"context": 200000, "cost_input": 0.00025, "cost_output": 0.00125},
    }

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.base_url = config.get("base_url", self.DEFAULT_BASE_URL)
        self.default_model = config.get("default_model", "claude-3-5-sonnet-20241022")

    async def complete(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs
    ) -> Dict[str, Any]:
        model = model or self.default_model

        # Convert messages to Anthropic format
        system_message = None
        anthropic_messages = []

        for msg in messages:
            if msg["role"] == "system":
                system_message = msg["content"]
            else:
                anthropic_messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            start_time = time.time()

            request_body = {
                "model": model,
                "messages": anthropic_messages,
                "max_tokens": max_tokens,
                "temperature": temperature,
            }

            if system_message:
                request_body["system"] = system_message

            response = await client.post(
                f"{self.base_url}/messages",
                headers={
                    "x-api-key": self.api_key,
                    "anthropic-version": "2023-06-01",
                    "Content-Type": "application/json"
                },
                json=request_body
            )

            latency_ms = int((time.time() - start_time) * 1000)

            if response.status_code != 200:
                return {
                    "success": False,
                    "error_code": str(response.status_code),
                    "error_message": response.text,
                    "latency_ms": latency_ms
                }

            data = response.json()
            usage = data.get("usage", {})

            model_info = self.MODELS.get(model, {"cost_input": 0, "cost_output": 0})
            input_cost = (usage.get("input_tokens", 0) / 1000) * model_info["cost_input"]
            output_cost = (usage.get("output_tokens", 0) / 1000) * model_info["cost_output"]

            content = ""
            if data.get("content"):
                for block in data["content"]:
                    if block.get("type") == "text":
                        content += block.get("text", "")

            return {
                "success": True,
                "content": content,
                "model": model,
                "input_tokens": usage.get("input_tokens", 0),
                "output_tokens": usage.get("output_tokens", 0),
                "total_tokens": usage.get("input_tokens", 0) + usage.get("output_tokens", 0),
                "estimated_cost": input_cost + output_cost,
                "finish_reason": data.get("stop_reason"),
                "latency_ms": latency_ms,
                "provider": "anthropic"
            }

    async def embed(
        self,
        texts: List[str],
        model: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        # Anthropic doesn't have a native embedding API
        return {
            "success": False,
            "error_code": "not_supported",
            "error_message": "Anthropic does not support embeddings. Use OpenAI or another provider.",
            "provider": "anthropic"
        }

    def estimate_tokens(self, text: str) -> int:
        # Rough approximation
        return len(text) // 4

    def get_available_models(self) -> List[Dict[str, Any]]:
        return [
            {
                "model_name": name,
                "context_window": info["context"],
                "cost_per_1k_input": info["cost_input"],
                "cost_per_1k_output": info["cost_output"],
                "capabilities": ["chat"]
            }
            for name, info in self.MODELS.items()
        ]


class AzureOpenAIProvider(AIProviderBase):
    """Azure OpenAI API provider"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.resource_name = config.get("azure_resource_name")
        self.deployment_id = config.get("azure_deployment_id")
        self.api_version = config.get("api_version", "2024-02-15-preview")
        self.base_url = f"https://{self.resource_name}.openai.azure.com"
        self.default_model = config.get("default_model", self.deployment_id)

    async def complete(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs
    ) -> Dict[str, Any]:
        deployment = model or self.deployment_id

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            start_time = time.time()

            response = await client.post(
                f"{self.base_url}/openai/deployments/{deployment}/chat/completions?api-version={self.api_version}",
                headers={
                    "api-key": self.api_key,
                    "Content-Type": "application/json"
                },
                json={
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    **kwargs
                }
            )

            latency_ms = int((time.time() - start_time) * 1000)

            if response.status_code != 200:
                return {
                    "success": False,
                    "error_code": str(response.status_code),
                    "error_message": response.text,
                    "latency_ms": latency_ms
                }

            data = response.json()
            usage = data.get("usage", {})

            return {
                "success": True,
                "content": data["choices"][0]["message"]["content"],
                "model": deployment,
                "input_tokens": usage.get("prompt_tokens", 0),
                "output_tokens": usage.get("completion_tokens", 0),
                "total_tokens": usage.get("total_tokens", 0),
                "estimated_cost": 0,  # Azure pricing varies by deployment
                "finish_reason": data["choices"][0].get("finish_reason"),
                "latency_ms": latency_ms,
                "provider": "azure_openai"
            }

    async def embed(
        self,
        texts: List[str],
        model: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        deployment = model or "text-embedding-ada-002"

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            start_time = time.time()

            response = await client.post(
                f"{self.base_url}/openai/deployments/{deployment}/embeddings?api-version={self.api_version}",
                headers={
                    "api-key": self.api_key,
                    "Content-Type": "application/json"
                },
                json={
                    "input": texts,
                    **kwargs
                }
            )

            latency_ms = int((time.time() - start_time) * 1000)

            if response.status_code != 200:
                return {
                    "success": False,
                    "error_code": str(response.status_code),
                    "error_message": response.text,
                    "latency_ms": latency_ms
                }

            data = response.json()

            return {
                "success": True,
                "embeddings": [item["embedding"] for item in data["data"]],
                "model": deployment,
                "total_tokens": data.get("usage", {}).get("total_tokens", 0),
                "latency_ms": latency_ms,
                "provider": "azure_openai"
            }

    def estimate_tokens(self, text: str) -> int:
        return len(text) // 4

    def get_available_models(self) -> List[Dict[str, Any]]:
        return [{"model_name": self.deployment_id, "capabilities": ["chat"]}]


class GoogleProvider(AIProviderBase):
    """Google Gemini API provider"""

    DEFAULT_BASE_URL = "https://generativelanguage.googleapis.com/v1beta"

    MODELS = {
        "gemini-1.5-pro": {"context": 2097152, "cost_input": 0.00125, "cost_output": 0.005},
        "gemini-1.5-flash": {"context": 1048576, "cost_input": 0.000075, "cost_output": 0.0003},
        "gemini-1.0-pro": {"context": 32760, "cost_input": 0.0005, "cost_output": 0.0015},
    }

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.base_url = config.get("base_url", self.DEFAULT_BASE_URL)
        self.default_model = config.get("default_model", "gemini-1.5-flash")

    async def complete(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs
    ) -> Dict[str, Any]:
        model = model or self.default_model

        # Convert messages to Gemini format
        contents = []
        system_instruction = None

        for msg in messages:
            if msg["role"] == "system":
                system_instruction = msg["content"]
            else:
                role = "user" if msg["role"] == "user" else "model"
                contents.append({
                    "role": role,
                    "parts": [{"text": msg["content"]}]
                })

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            start_time = time.time()

            request_body = {
                "contents": contents,
                "generationConfig": {
                    "temperature": temperature,
                    "maxOutputTokens": max_tokens,
                }
            }

            if system_instruction:
                request_body["systemInstruction"] = {"parts": [{"text": system_instruction}]}

            response = await client.post(
                f"{self.base_url}/models/{model}:generateContent?key={self.api_key}",
                headers={"Content-Type": "application/json"},
                json=request_body
            )

            latency_ms = int((time.time() - start_time) * 1000)

            if response.status_code != 200:
                return {
                    "success": False,
                    "error_code": str(response.status_code),
                    "error_message": response.text,
                    "latency_ms": latency_ms
                }

            data = response.json()

            content = ""
            if data.get("candidates"):
                for part in data["candidates"][0].get("content", {}).get("parts", []):
                    content += part.get("text", "")

            usage = data.get("usageMetadata", {})

            model_info = self.MODELS.get(model, {"cost_input": 0, "cost_output": 0})
            input_cost = (usage.get("promptTokenCount", 0) / 1000) * model_info["cost_input"]
            output_cost = (usage.get("candidatesTokenCount", 0) / 1000) * model_info["cost_output"]

            return {
                "success": True,
                "content": content,
                "model": model,
                "input_tokens": usage.get("promptTokenCount", 0),
                "output_tokens": usage.get("candidatesTokenCount", 0),
                "total_tokens": usage.get("totalTokenCount", 0),
                "estimated_cost": input_cost + output_cost,
                "finish_reason": data.get("candidates", [{}])[0].get("finishReason"),
                "latency_ms": latency_ms,
                "provider": "google"
            }

    async def embed(
        self,
        texts: List[str],
        model: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        model = model or "text-embedding-004"

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            start_time = time.time()

            response = await client.post(
                f"{self.base_url}/models/{model}:embedContent?key={self.api_key}",
                headers={"Content-Type": "application/json"},
                json={
                    "content": {"parts": [{"text": text}]} if len(texts) == 1 else texts,
                }
            )

            latency_ms = int((time.time() - start_time) * 1000)

            if response.status_code != 200:
                return {
                    "success": False,
                    "error_code": str(response.status_code),
                    "error_message": response.text,
                    "latency_ms": latency_ms
                }

            data = response.json()

            return {
                "success": True,
                "embeddings": [data.get("embedding", {}).get("values", [])],
                "model": model,
                "total_tokens": 0,
                "latency_ms": latency_ms,
                "provider": "google"
            }

    def estimate_tokens(self, text: str) -> int:
        return len(text) // 4

    def get_available_models(self) -> List[Dict[str, Any]]:
        return [
            {
                "model_name": name,
                "context_window": info["context"],
                "cost_per_1k_input": info["cost_input"],
                "cost_per_1k_output": info["cost_output"],
                "capabilities": ["chat"]
            }
            for name, info in self.MODELS.items()
        ]


class LocalProvider(AIProviderBase):
    """Local/Self-hosted LLM provider (Ollama, vLLM, etc.)"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.base_url = config.get("base_url", "http://localhost:11434")
        self.default_model = config.get("default_model", "llama3.2")
        self.provider_type = config.get("local_type", "ollama")  # ollama, vllm, llamacpp

    async def complete(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs
    ) -> Dict[str, Any]:
        model = model or self.default_model

        if self.provider_type == "ollama":
            return await self._ollama_complete(messages, model, temperature, max_tokens, **kwargs)
        else:
            # OpenAI-compatible API (vLLM, llamacpp server, etc.)
            return await self._openai_compatible_complete(messages, model, temperature, max_tokens, **kwargs)

    async def _ollama_complete(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float,
        max_tokens: int,
        **kwargs
    ) -> Dict[str, Any]:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            start_time = time.time()

            response = await client.post(
                f"{self.base_url}/api/chat",
                json={
                    "model": model,
                    "messages": messages,
                    "stream": False,
                    "options": {
                        "temperature": temperature,
                        "num_predict": max_tokens,
                    }
                }
            )

            latency_ms = int((time.time() - start_time) * 1000)

            if response.status_code != 200:
                return {
                    "success": False,
                    "error_code": str(response.status_code),
                    "error_message": response.text,
                    "latency_ms": latency_ms
                }

            data = response.json()

            return {
                "success": True,
                "content": data.get("message", {}).get("content", ""),
                "model": model,
                "input_tokens": data.get("prompt_eval_count", 0),
                "output_tokens": data.get("eval_count", 0),
                "total_tokens": data.get("prompt_eval_count", 0) + data.get("eval_count", 0),
                "estimated_cost": 0,  # Local models are free
                "finish_reason": "stop",
                "latency_ms": latency_ms,
                "provider": "local_ollama"
            }

    async def _openai_compatible_complete(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float,
        max_tokens: int,
        **kwargs
    ) -> Dict[str, Any]:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            start_time = time.time()

            headers = {"Content-Type": "application/json"}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"

            response = await client.post(
                f"{self.base_url}/v1/chat/completions",
                headers=headers,
                json={
                    "model": model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    **kwargs
                }
            )

            latency_ms = int((time.time() - start_time) * 1000)

            if response.status_code != 200:
                return {
                    "success": False,
                    "error_code": str(response.status_code),
                    "error_message": response.text,
                    "latency_ms": latency_ms
                }

            data = response.json()
            usage = data.get("usage", {})

            return {
                "success": True,
                "content": data["choices"][0]["message"]["content"],
                "model": model,
                "input_tokens": usage.get("prompt_tokens", 0),
                "output_tokens": usage.get("completion_tokens", 0),
                "total_tokens": usage.get("total_tokens", 0),
                "estimated_cost": 0,
                "finish_reason": data["choices"][0].get("finish_reason"),
                "latency_ms": latency_ms,
                "provider": f"local_{self.provider_type}"
            }

    async def embed(
        self,
        texts: List[str],
        model: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        model = model or "nomic-embed-text"

        if self.provider_type == "ollama":
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                embeddings = []

                for text in texts:
                    start_time = time.time()

                    response = await client.post(
                        f"{self.base_url}/api/embeddings",
                        json={"model": model, "prompt": text}
                    )

                    if response.status_code != 200:
                        return {
                            "success": False,
                            "error_code": str(response.status_code),
                            "error_message": response.text,
                        }

                    data = response.json()
                    embeddings.append(data.get("embedding", []))

                return {
                    "success": True,
                    "embeddings": embeddings,
                    "model": model,
                    "total_tokens": 0,
                    "latency_ms": int((time.time() - start_time) * 1000),
                    "provider": "local_ollama"
                }

        return {
            "success": False,
            "error_code": "not_supported",
            "error_message": "Embeddings not supported for this local provider configuration"
        }

    def estimate_tokens(self, text: str) -> int:
        return len(text) // 4

    def get_available_models(self) -> List[Dict[str, Any]]:
        return [{"model_name": self.default_model, "capabilities": ["chat"]}]


# ============================================================================
# AI Service Manager
# ============================================================================

class AIService:
    """
    Central AI service that manages multiple providers and routes requests.
    """

    PROVIDER_CLASSES = {
        "openai": OpenAIProvider,
        "anthropic": AnthropicProvider,
        "azure_openai": AzureOpenAIProvider,
        "google": GoogleProvider,
        "local": LocalProvider,
    }

    def __init__(self):
        self.providers: Dict[str, AIProviderBase] = {}
        self.default_provider: Optional[str] = None
        self.request_log: List[Dict[str, Any]] = []

    def register_provider(
        self,
        provider_id: str,
        provider_type: str,
        config: Dict[str, Any],
        is_default: bool = False
    ) -> bool:
        """Register a new AI provider"""
        if provider_type not in self.PROVIDER_CLASSES:
            return False

        provider_class = self.PROVIDER_CLASSES[provider_type]
        self.providers[provider_id] = provider_class(config)

        if is_default or not self.default_provider:
            self.default_provider = provider_id

        return True

    def remove_provider(self, provider_id: str) -> bool:
        """Remove a provider"""
        if provider_id in self.providers:
            del self.providers[provider_id]
            if self.default_provider == provider_id:
                self.default_provider = next(iter(self.providers.keys()), None)
            return True
        return False

    def get_provider(self, provider_id: Optional[str] = None) -> Optional[AIProviderBase]:
        """Get a provider by ID or return default"""
        if provider_id:
            return self.providers.get(provider_id)
        if self.default_provider:
            return self.providers.get(self.default_provider)
        return None

    async def complete(
        self,
        messages: List[Dict[str, str]],
        provider_id: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        capability_name: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate a completion using the specified or default provider.
        """
        provider = self.get_provider(provider_id)
        if not provider:
            return {
                "success": False,
                "error_code": "no_provider",
                "error_message": "No AI provider configured"
            }

        request_id = str(uuid.uuid4())[:8]
        start_time = time.time()

        # Generate prompt hash for tracking
        prompt_text = json.dumps(messages)
        prompt_hash = hashlib.sha256(prompt_text.encode()).hexdigest()[:16]

        result = await provider.complete(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )

        # Log the request
        log_entry = {
            "request_id": request_id,
            "provider_id": provider_id or self.default_provider,
            "capability_name": capability_name,
            "model": result.get("model"),
            "prompt_hash": prompt_hash,
            "input_tokens": result.get("input_tokens", 0),
            "output_tokens": result.get("output_tokens", 0),
            "total_tokens": result.get("total_tokens", 0),
            "estimated_cost": result.get("estimated_cost", 0),
            "latency_ms": result.get("latency_ms", 0),
            "success": result.get("success", False),
            "error_code": result.get("error_code"),
            "timestamp": datetime.utcnow().isoformat(),
            "context": context
        }
        self.request_log.append(log_entry)

        result["request_id"] = request_id
        return result

    async def embed(
        self,
        texts: List[str],
        provider_id: Optional[str] = None,
        model: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate embeddings using the specified or default provider."""
        provider = self.get_provider(provider_id)
        if not provider:
            return {
                "success": False,
                "error_code": "no_provider",
                "error_message": "No AI provider configured"
            }

        return await provider.embed(texts=texts, model=model, **kwargs)

    def get_usage_summary(self) -> Dict[str, Any]:
        """Get usage summary from request log"""
        if not self.request_log:
            return {
                "total_requests": 0,
                "successful_requests": 0,
                "failed_requests": 0,
                "total_tokens": 0,
                "total_cost": 0,
                "avg_latency_ms": 0
            }

        successful = [r for r in self.request_log if r.get("success")]
        failed = [r for r in self.request_log if not r.get("success")]

        total_tokens = sum(r.get("total_tokens", 0) for r in self.request_log)
        total_cost = sum(r.get("estimated_cost", 0) for r in self.request_log)
        latencies = [r.get("latency_ms", 0) for r in self.request_log if r.get("latency_ms")]

        return {
            "total_requests": len(self.request_log),
            "successful_requests": len(successful),
            "failed_requests": len(failed),
            "total_tokens": total_tokens,
            "total_input_tokens": sum(r.get("input_tokens", 0) for r in self.request_log),
            "total_output_tokens": sum(r.get("output_tokens", 0) for r in self.request_log),
            "total_cost": round(total_cost, 6),
            "avg_latency_ms": round(sum(latencies) / len(latencies), 2) if latencies else 0,
            "by_provider": self._group_by_provider(),
            "by_capability": self._group_by_capability()
        }

    def _group_by_provider(self) -> Dict[str, Dict[str, Any]]:
        """Group usage by provider"""
        result = {}
        for entry in self.request_log:
            provider = entry.get("provider_id", "unknown")
            if provider not in result:
                result[provider] = {
                    "requests": 0,
                    "tokens": 0,
                    "cost": 0
                }
            result[provider]["requests"] += 1
            result[provider]["tokens"] += entry.get("total_tokens", 0)
            result[provider]["cost"] += entry.get("estimated_cost", 0)
        return result

    def _group_by_capability(self) -> Dict[str, Dict[str, Any]]:
        """Group usage by capability"""
        result = {}
        for entry in self.request_log:
            capability = entry.get("capability_name", "unknown")
            if capability not in result:
                result[capability] = {
                    "requests": 0,
                    "tokens": 0,
                    "cost": 0
                }
            result[capability]["requests"] += 1
            result[capability]["tokens"] += entry.get("total_tokens", 0)
            result[capability]["cost"] += entry.get("estimated_cost", 0)
        return result

    async def health_check(self, provider_id: Optional[str] = None) -> Dict[str, Any]:
        """Check health of a provider"""
        provider = self.get_provider(provider_id)
        if not provider:
            return {"status": "error", "message": "Provider not found"}

        try:
            result = await provider.complete(
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=10
            )

            if result.get("success"):
                return {
                    "status": "healthy",
                    "latency_ms": result.get("latency_ms"),
                    "provider": result.get("provider")
                }
            else:
                return {
                    "status": "unhealthy",
                    "error": result.get("error_message")
                }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }


# ============================================================================
# Capability-Specific AI Functions
# ============================================================================

async def ai_market_research(
    ai_service: AIService,
    input_data: Dict[str, Any],
    context: Dict[str, Any]
) -> Dict[str, Any]:
    """Execute market research using AI"""
    messages = [
        {
            "role": "system",
            "content": """You are a market research analyst. Analyze the given topic and provide:
1. Market Overview - Size, growth rate, key trends
2. Competitive Landscape - Major players, market share
3. Target Segments - Customer segments, needs
4. Opportunities - Growth opportunities, emerging trends
5. Risks - Market risks, barriers to entry

Provide data-driven insights with specific metrics where possible."""
        },
        {
            "role": "user",
            "content": f"Conduct market research on: {input_data.get('topic', 'general market')}\n\nFocus areas: {input_data.get('focus_areas', 'overall market dynamics')}\n\nContext: {json.dumps(input_data.get('context', {}))}"
        }
    ]

    result = await ai_service.complete(
        messages=messages,
        capability_name="market_research",
        context=context,
        temperature=0.7,
        max_tokens=2000
    )

    return {
        "capability": "market_research",
        "success": result.get("success", False),
        "analysis": result.get("content", ""),
        "tokens_used": result.get("total_tokens", 0),
        "cost": result.get("estimated_cost", 0),
        "request_id": result.get("request_id")
    }


async def ai_financial_modeling(
    ai_service: AIService,
    input_data: Dict[str, Any],
    context: Dict[str, Any]
) -> Dict[str, Any]:
    """Execute financial modeling using AI"""
    messages = [
        {
            "role": "system",
            "content": """You are a financial analyst. Create financial models and projections based on the input data.
Include:
1. Revenue projections with assumptions
2. Cost analysis and breakdown
3. Profitability metrics (gross margin, EBITDA, net income)
4. Cash flow projections
5. Key financial ratios
6. Sensitivity analysis

Format numbers clearly and explain assumptions."""
        },
        {
            "role": "user",
            "content": f"Create a financial model for:\n{json.dumps(input_data, indent=2)}"
        }
    ]

    result = await ai_service.complete(
        messages=messages,
        capability_name="financial_modeling",
        context=context,
        temperature=0.3,
        max_tokens=2500
    )

    return {
        "capability": "financial_modeling",
        "success": result.get("success", False),
        "model": result.get("content", ""),
        "tokens_used": result.get("total_tokens", 0),
        "cost": result.get("estimated_cost", 0),
        "request_id": result.get("request_id")
    }


async def ai_content_generation(
    ai_service: AIService,
    input_data: Dict[str, Any],
    context: Dict[str, Any]
) -> Dict[str, Any]:
    """Generate content using AI"""
    content_type = input_data.get("content_type", "article")
    tone = input_data.get("tone", "professional")

    messages = [
        {
            "role": "system",
            "content": f"""You are a content writer specializing in {content_type} content.
Write in a {tone} tone. Create engaging, well-structured content that:
- Has a clear headline/title
- Uses proper formatting (headings, lists, paragraphs)
- Is SEO-friendly with natural keyword usage
- Includes a call-to-action where appropriate"""
        },
        {
            "role": "user",
            "content": f"Create {content_type} content about: {input_data.get('topic', '')}\n\nKey points to cover: {input_data.get('key_points', [])}\n\nTarget audience: {input_data.get('audience', 'general')}\n\nWord count: ~{input_data.get('word_count', 500)} words"
        }
    ]

    result = await ai_service.complete(
        messages=messages,
        capability_name="content_generation",
        context=context,
        temperature=0.8,
        max_tokens=2000
    )

    return {
        "capability": "content_generation",
        "success": result.get("success", False),
        "content": result.get("content", ""),
        "tokens_used": result.get("total_tokens", 0),
        "cost": result.get("estimated_cost", 0),
        "request_id": result.get("request_id")
    }


async def ai_data_analysis(
    ai_service: AIService,
    input_data: Dict[str, Any],
    context: Dict[str, Any]
) -> Dict[str, Any]:
    """Analyze data using AI"""
    messages = [
        {
            "role": "system",
            "content": """You are a data analyst. Analyze the provided data and deliver:
1. Summary Statistics - Key metrics and distributions
2. Patterns & Trends - Notable patterns in the data
3. Correlations - Relationships between variables
4. Anomalies - Outliers or unusual data points
5. Insights - Actionable business insights
6. Recommendations - Data-driven recommendations

Use clear visualizations descriptions and specific numbers."""
        },
        {
            "role": "user",
            "content": f"Analyze this data:\n{json.dumps(input_data.get('data', {}), indent=2)}\n\nAnalysis focus: {input_data.get('focus', 'general analysis')}"
        }
    ]

    result = await ai_service.complete(
        messages=messages,
        capability_name="data_analysis",
        context=context,
        temperature=0.3,
        max_tokens=2000
    )

    return {
        "capability": "data_analysis",
        "success": result.get("success", False),
        "analysis": result.get("content", ""),
        "tokens_used": result.get("total_tokens", 0),
        "cost": result.get("estimated_cost", 0),
        "request_id": result.get("request_id")
    }


async def ai_document_processing(
    ai_service: AIService,
    input_data: Dict[str, Any],
    context: Dict[str, Any]
) -> Dict[str, Any]:
    """Process documents using AI"""
    action = input_data.get("action", "summarize")

    action_prompts = {
        "summarize": "Provide a concise summary of this document, highlighting key points and conclusions.",
        "extract": "Extract key information including dates, names, numbers, and important facts.",
        "classify": "Classify this document by type, topic, sentiment, and urgency.",
        "translate": f"Translate this document to {input_data.get('target_language', 'English')}.",
        "rewrite": f"Rewrite this document in a {input_data.get('style', 'professional')} style."
    }

    messages = [
        {
            "role": "system",
            "content": f"You are a document processing specialist. {action_prompts.get(action, action_prompts['summarize'])}"
        },
        {
            "role": "user",
            "content": f"Document content:\n\n{input_data.get('content', '')}"
        }
    ]

    result = await ai_service.complete(
        messages=messages,
        capability_name="document_processing",
        context=context,
        temperature=0.3,
        max_tokens=2000
    )

    return {
        "capability": "document_processing",
        "action": action,
        "success": result.get("success", False),
        "result": result.get("content", ""),
        "tokens_used": result.get("total_tokens", 0),
        "cost": result.get("estimated_cost", 0),
        "request_id": result.get("request_id")
    }


async def ai_code_generation(
    ai_service: AIService,
    input_data: Dict[str, Any],
    context: Dict[str, Any]
) -> Dict[str, Any]:
    """Generate code using AI"""
    language = input_data.get("language", "python")

    messages = [
        {
            "role": "system",
            "content": f"""You are an expert {language} developer. Write clean, well-documented, production-ready code.
Follow best practices:
- Include docstrings and comments
- Handle errors appropriately
- Use meaningful variable names
- Follow language conventions
- Include type hints where applicable"""
        },
        {
            "role": "user",
            "content": f"Write {language} code for: {input_data.get('description', '')}\n\nRequirements:\n{json.dumps(input_data.get('requirements', []))}\n\nConstraints:\n{json.dumps(input_data.get('constraints', []))}"
        }
    ]

    result = await ai_service.complete(
        messages=messages,
        capability_name="code_generation",
        context=context,
        temperature=0.3,
        max_tokens=3000
    )

    return {
        "capability": "code_generation",
        "language": language,
        "success": result.get("success", False),
        "code": result.get("content", ""),
        "tokens_used": result.get("total_tokens", 0),
        "cost": result.get("estimated_cost", 0),
        "request_id": result.get("request_id")
    }


# Mapping of capability names to their AI functions
AI_CAPABILITY_FUNCTIONS = {
    "market_research": ai_market_research,
    "trend_analysis": ai_market_research,  # Reuse with different prompt
    "competitive_intelligence": ai_market_research,
    "financial_modeling": ai_financial_modeling,
    "budget_planning": ai_financial_modeling,
    "forecasting": ai_financial_modeling,
    "content_generation": ai_content_generation,
    "document_processing": ai_document_processing,
    "data_analysis": ai_data_analysis,
    "code_generation": ai_code_generation,
}


async def execute_ai_capability(
    ai_service: AIService,
    capability_name: str,
    input_data: Dict[str, Any],
    context: Dict[str, Any]
) -> Dict[str, Any]:
    """Execute an AI capability by name"""
    if capability_name in AI_CAPABILITY_FUNCTIONS:
        return await AI_CAPABILITY_FUNCTIONS[capability_name](ai_service, input_data, context)

    # Generic capability execution
    messages = [
        {
            "role": "system",
            "content": f"You are an AI assistant specialized in {capability_name.replace('_', ' ')}. Complete the requested task thoroughly and professionally."
        },
        {
            "role": "user",
            "content": f"Execute {capability_name} capability with input:\n{json.dumps(input_data, indent=2)}"
        }
    ]

    result = await ai_service.complete(
        messages=messages,
        capability_name=capability_name,
        context=context,
        temperature=0.7,
        max_tokens=2000
    )

    return {
        "capability": capability_name,
        "success": result.get("success", False),
        "result": result.get("content", ""),
        "tokens_used": result.get("total_tokens", 0),
        "cost": result.get("estimated_cost", 0),
        "request_id": result.get("request_id")
    }


# Global AI service instance
ai_service = AIService()


def init_ai_service_from_env():
    """Initialize AI service from environment variables"""
    # OpenAI
    if os.getenv("OPENAI_API_KEY"):
        ai_service.register_provider(
            provider_id="openai",
            provider_type="openai",
            config={
                "api_key": os.getenv("OPENAI_API_KEY"),
                "default_model": os.getenv("OPENAI_MODEL", "gpt-4o-mini")
            },
            is_default=True
        )

    # Anthropic
    if os.getenv("ANTHROPIC_API_KEY"):
        ai_service.register_provider(
            provider_id="anthropic",
            provider_type="anthropic",
            config={
                "api_key": os.getenv("ANTHROPIC_API_KEY"),
                "default_model": os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022")
            }
        )

    # Azure OpenAI
    if os.getenv("AZURE_OPENAI_API_KEY"):
        ai_service.register_provider(
            provider_id="azure",
            provider_type="azure_openai",
            config={
                "api_key": os.getenv("AZURE_OPENAI_API_KEY"),
                "azure_resource_name": os.getenv("AZURE_OPENAI_RESOURCE"),
                "azure_deployment_id": os.getenv("AZURE_OPENAI_DEPLOYMENT"),
                "api_version": os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")
            }
        )

    # Google
    if os.getenv("GOOGLE_API_KEY"):
        ai_service.register_provider(
            provider_id="google",
            provider_type="google",
            config={
                "api_key": os.getenv("GOOGLE_API_KEY"),
                "default_model": os.getenv("GOOGLE_MODEL", "gemini-1.5-flash")
            }
        )

    # Local (Ollama)
    if os.getenv("OLLAMA_HOST"):
        ai_service.register_provider(
            provider_id="local",
            provider_type="local",
            config={
                "base_url": os.getenv("OLLAMA_HOST", "http://localhost:11434"),
                "default_model": os.getenv("OLLAMA_MODEL", "llama3.2"),
                "local_type": "ollama"
            }
        )

    return ai_service
