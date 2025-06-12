# -*- coding: utf-8 -*-
"""Helpers for retrieving available models from OpenAI-compatible APIs."""

from __future__ import annotations

import os
from typing import List

from openai import OpenAI, AzureOpenAI


def _create_client(provider: str):
    """Create an OpenAI client for the given provider."""
    provider = provider.lower()
    api_key = os.getenv(f"{provider.upper()}_API_KEY") or os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError(f"No API key configured for provider: {provider}")

    base_url = os.getenv(f"{provider.upper()}_BASE_URL") or os.getenv("OPENAI_BASE_URL")

    headers: dict[str, str] = {}
    if os.getenv("OPENAI_ORGANIZATION"):
        headers["OpenAI-Organization"] = os.getenv("OPENAI_ORGANIZATION")
    if os.getenv("OPENAI_PROJECT"):
        headers["OpenAI-Project"] = os.getenv("OPENAI_PROJECT")

    timeout_ms = os.getenv("OPENAI_TIMEOUT_MS")
    timeout = int(timeout_ms) if timeout_ms and timeout_ms.isdigit() else None

    if provider == "azure":
        api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2025-03-01-preview")
        return AzureOpenAI(
            api_key=api_key,
            base_url=base_url,
            api_version=api_version,
            timeout=timeout,
            default_headers=headers,
        )

    return OpenAI(
        api_key=api_key, base_url=base_url, timeout=timeout, default_headers=headers
    )


def get_available_models(provider: str) -> List[str]:
    """Return a list of model identifiers available for the API key."""
    client = _create_client(provider)
    try:
        result = client.models.list()
        models: list[str] = []
        data = getattr(result, "data", result)
        for model in data:
            model_id = getattr(model, "id", None)
            if isinstance(model_id, str):
                if model_id.startswith("models/"):
                    model_id = model_id.replace("models/", "")
                models.append(model_id)
        models.sort()
        return models
    except Exception:
        return []
