"""Interfaces module - Abstract base classes for SOLID principles."""

from .browser import IBrowserAutomation
from .analyzer import IDOMAnalyzer, IInteractionDetector
from .llm import ILLMProvider, IGherkinGenerator
from .output import IFeatureWriter

__all__ = [
    'IBrowserAutomation',
    'IDOMAnalyzer',
    'IInteractionDetector',
    'ILLMProvider',
    'IGherkinGenerator',
    'IFeatureWriter'
]
