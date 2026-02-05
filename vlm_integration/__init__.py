"""
VLM Integration Package
=======================

This package provides Vision-Language Model integration for the
Dynamic Dashboard AI application using Ollama + LLaVA.

Modules:
- vlm_client: Core client for Ollama VLM API
- prompt_templates: Prompt templates for financial analysis
- image_processor: Image handling and preprocessing

Usage:
    from vlm_integration.vlm_client import get_vlm_client
    
    client = get_vlm_client()
    result = client.chat("What's the gold trend?", "/path/to/snapshot.png")
"""

from .vlm_client import OllamaVLMClient, get_vlm_client
from .prompt_templates import PromptTemplates
from .image_processor import ImageProcessor, get_latest_snapshot_path

__all__ = [
    'OllamaVLMClient',
    'get_vlm_client',
    'PromptTemplates',
    'ImageProcessor',
    'get_latest_snapshot_path',
]
