# app/core/registry.py
#
# ═══════════════════════════════════════════════════════════════════════════
# PROVIDER REGISTRY — The Plugin Discovery Engine
# ═══════════════════════════════════════════════════════════════════════════
#
# This module automatically discovers and loads Data and Knowledge providers.
#
# How it works:
#   1. It scans the /providers/ folders for .py files.
#   2. It dynamically imports those modules.
#   3. It finds any class that inherits from BaseDataProvider or BaseKnowledgeProvider.
#   4. It initializes them and returns a list to the Dispatcher.
#
# This makes adding a new data source as simple as dropping a file in a folder.
#
# ═══════════════════════════════════════════════════════════════════════════

import importlib
import inspect
import json
import os
import pkgutil
from pathlib import Path
from typing import List, Type, Any

from app.core.base import BaseDataProvider, BaseKnowledgeProvider


class ProviderRegistry:
    """
    Scans directories and automatically registers provider classes.
    """

    @staticmethod
    def discover_providers(package_path: str, base_class: Type) -> List[Any]:
        """
        Dynamically find and instantiate all provider classes in a package.
        
        Args:
            package_path: Dot-notation path to the package (e.g. 'app.providers.data')
            base_class: The interface class to look for (e.g. BaseDataProvider)
        """
        providers = []
        
        # 1. Get the physical path of the package
        try:
            package = importlib.import_module(package_path)
            if not hasattr(package, '__file__') or package.__file__ is None:
                # Fallback: construct path from current working directory
                package_dir = os.path.join(os.getcwd(), *package_path.split('.'))
            else:
                package_dir = os.path.dirname(package.__file__)
        except ImportError:
            print(f"⚠️ [Registry] Could not find package: {package_path}")
            return []

        # 2. Iterate through all modules (.py files) in the directory
        for _, module_name, is_pkg in pkgutil.iter_modules([package_dir]):
            if is_pkg:
                continue  # skip sub-directories
            
            # Full module path: 'app.providers.data.rte_provider'
            full_module_path = f"{package_path}.{module_name}"
            
            try:
                module = importlib.import_module(full_module_path)
                
                # 3. Find classes in this module that inherit from base_class
                for name, obj in inspect.getmembers(module, inspect.isclass):
                    # Check if it's a subclass of the base, and NOT the base itself
                    if issubclass(obj, base_class) and obj is not base_class:
                        print(f"🔌 [Registry] Discovered: {name} in {full_module_path}")
                        try:
                            # 4. Instantiate the provider
                            providers.append(obj())
                        except Exception as e:
                            print(f"❌ [Registry] Failed to init {name}: {e}")
            
            except Exception as e:
                print(f"❌ [Registry] Error loading module {full_module_path}: {e}")

        return providers

    @classmethod
    def load_all_data_providers(cls) -> List[BaseDataProvider]:
        """
        Auto-load everything in app/providers/data/ AND dynamic sources from config.
        """
        # 1. Discover hardcoded Python providers (like RTEDataProvider)
        providers = cls.discover_providers("app.providers.data", BaseDataProvider)

        # 2. Discover dynamic sources added via the UI (stored in sources.json)
        from app.config.sources import CONFIG_PATH
        from app.providers.data.dynamic_api_provider import DynamicAPIProvider
        try:
            if os.path.exists(CONFIG_PATH):
                with open(CONFIG_PATH, 'r') as f:
                    config = json.load(f)
                    for source in config.get("data_sources", []):
                        if source.get("enabled"):
                            print(f"🌐 [Registry] Loading Dynamic Source: {source['name']}")
                            providers.append(DynamicAPIProvider(source_id=source['id']))
        except Exception as e:
            print(f"⚠️ [Registry] Failed to load dynamic sources: {e}")

        return providers

    @classmethod
    def load_all_knowledge_providers(cls) -> List[BaseKnowledgeProvider]:
        """Auto-load everything in app/providers/knowledge/"""
        return cls.discover_providers("app.providers.knowledge", BaseKnowledgeProvider)
