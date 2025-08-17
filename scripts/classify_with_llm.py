#!/usr/bin/env python3
"""
Utility script to classify email messages using a local large language
model (LLM) served by Ollama or, optionally, a remote OpenAI model.  This
script is intended to be called by the n8n workflow via an HTTP node or
manually from the command line when testing classification prompts.

The classifier looks at the sender, subject and an optional snippet of
the body and returns a number between 1 and 4 indicating the category:

1 — Personal or Important
2 — Promotional or Notification
3 — Newsletter
4 — Unimportant Junk

The environment variables OLLAMA_ENDPOINT and OLLAMA_MODEL determine
which local model to use.  If OPENAI_API_KEY is provided the script
will fall back to OpenAI's API for classification when the local model
is unavailable.
"""

import os
import sys
import json
from typing import Optional

try:
    import requests  # type: ignore
except ImportError:
    sys.stderr.write(
        "Error: The 'requests' library is required. Install it with 'pip install requests'.\n"
    )
    raise


def classify_email(
    sender: str,
    subject: str,
    body_snippet: str = "",
    *,
    ollama_endpoint: Optional[str] = None,
    ollama_model: Optional[str] = None,
    openai_api_key: Optional[str] = None,
) -> str:
    """Classify an email using a local LLM via Ollama or OpenAI API.

    Args:
        sender: Email address of the sender.
        subject: Subject line of the email.
        body_snippet: Optional snippet of the email body (first 200 chars).
        ollama_endpoint: Base URL of the local Ollama server.
        ollama_model: Name of the model to use on Ollama.
        openai_api_key: API key for OpenAI (optional fallback).

    Returns:
        A string representing the classification category ("1"–"4").
    """
    prompt = (
        "You are an email classifier. Given the sender address, subject line,"
        " and a short snippet of the email body, classify the message into one"
        " of four categories.\n"
        "\n"
        "Return ONLY the number corresponding to the correct category: \n"
        "1 — Personal or Important\n"
        "2 — Promotional or Notification\n"
        "3 — Newsletter\n"
        "4 — Unimportant Junk\n"
        "\n"
        f"Sender: {sender}\n"
        f"Subject: {subject}\n"
        f"Body: {body_snippet}\n"
        "\n"
        "Classification:"
    )

    # Use environment defaults if arguments are not provided
    if ollama_endpoint is None:
        ollama_endpoint = os.getenv("OLLAMA_ENDPOINT", "http://localhost:11434")
    if ollama_model is None:
        ollama_model = os.getenv("OLLAMA_MODEL", "llama3")
    if openai_api_key is None:
        openai_api_key = os.getenv("OPENAI_API_KEY")

    # Attempt classification via Ollama
    try:
        response = requests.post(
            f"{ollama_endpoint.rstrip('/')}/api/generate",
            json={"model": ollama_model, "prompt": prompt, "stream": False},
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()
        # The response from Ollama's generate API typically contains the
        # generated text in the 'response' field.
        result = data.get("response", "").strip().split()[0]
        return result
    except Exception as exc:
        # Fall back to OpenAI if configured
        if openai_api_key:
            try:
                return classify_with_openai(
                    prompt, api_key=openai_api_key, model="gpt-4-turbo"
                )
            except Exception:
                # If even the fallback fails, re-raise the original error
                raise exc
        else:
            raise exc


def classify_with_openai(prompt: str, *, api_key: str, model: str = "gpt-4-turbo") -> str:
    """Classify using OpenAI's chat completions endpoint.  This is used as a
    fallback when a local model is not available or fails.
    """
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.0,
        "max_tokens": 1,
    }
    response = requests.post(url, headers=headers, json=payload, timeout=30)
    response.raise_for_status()
    data = response.json()
    content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
    return content.strip().split()[0]


def main() -> None:
    """Entry point when run from the command line."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Classify an email using a local LLM or OpenAI."
    )
    parser.add_argument("--sender", required=True, help="Sender email address")
    parser.add_argument("--subject", required=True, help="Email subject line")
    parser.add_argument(
        "--body",
        default="",
        help="Optional snippet from the body (first 200 characters)",
    )
    args = parser.parse_args()
    category = classify_email(args.sender, args.subject, args.body)
    print(category)


if __name__ == "__main__":
    main()
