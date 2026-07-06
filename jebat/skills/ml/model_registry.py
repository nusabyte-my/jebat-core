"""
JEBAT Model Registry

Centralized model management:
- Model versioning
- Model storage
- Model deployment
- Performance tracking
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class ModelInfo:
    """Model metadata."""

    name: str
    version: str
    model_type: str
    created_at: datetime = field(default_factory=datetime.now)
    metrics: Dict[str, float] = field(default_factory=dict)
    path: str = ""
    status: str = "active"  # active, archived, deprecated
    tags: List[str] = field(default_factory=list)


class ModelRegistry:
    """
    Centralized Model Registry for JEBAT.

    Track, version, and manage all ML models.
    """

    def __init__(self, storage_path: str = "./models"):
        """
        Initialize Model Registry.

        Args:
            storage_path: Path to store models
        """
        self.storage_path = storage_path
        self.models: Dict[str, ModelInfo] = {}
        self.model_versions: Dict[str, List[ModelInfo]] = {}

        logger.info(f"ModelRegistry initialized (storage: {storage_path})")

    async def register(
        self,
        name: str,
        model_type: str,
        metrics: Dict[str, float],
        path: str = "",
        tags: Optional[List[str]] = None,
    ) -> ModelInfo:
        """
        Register a new model.

        Args:
            name: Model name
            model_type: Type of model
            metrics: Performance metrics
            path: Model file path
            tags: Optional tags

        Returns:
            ModelInfo
        """
        # Get version
        version = self._get_next_version(name)

        model = ModelInfo(
            name=name,
            version=version,
            model_type=model_type,
            metrics=metrics,
            path=path,
            tags=tags or [],
        )

        # Store in registry
        key = f"{name}:{version}"
        self.models[key] = model

        if name not in self.model_versions:
            self.model_versions[name] = []
        self.model_versions[name].append(model)

        logger.info(f"Registered model: {key}")

        return model

    def _get_next_version(self, name: str) -> str:
        """Get next version number."""
        if name not in self.model_versions:
            return "1.0.0"

        versions = self.model_versions[name]
        latest = versions[-1].version
        parts = latest.split(".")
        parts[-1] = str(int(parts[-1]) + 1)
        return ".".join(parts)

    async def get_model(
        self,
        name: str,
        version: Optional[str] = None,
    ) -> Optional[ModelInfo]:
        """
        Get model info.

        Args:
            name: Model name
            version: Specific version (latest if None)

        Returns:
            ModelInfo or None
        """
        if version:
            return self.models.get(f"{name}:{version}")

        # Get latest version
        if name in self.model_versions and self.model_versions[name]:
            return self.model_versions[name][-1]

        return None

    async def list_models(
        self,
        model_type: Optional[str] = None,
        status: Optional[str] = None,
    ) -> List[ModelInfo]:
        """
        List models with filters.

        Args:
            model_type: Filter by type
            status: Filter by status

        Returns:
            List of ModelInfo
        """
        models = list(self.models.values())

        if model_type:
            models = [m for m in models if m.model_type == model_type]

        if status:
            models = [m for m in models if m.status == status]

        return models

    async def deploy(
        self,
        name: str,
        version: str,
        endpoint: str,
    ) -> Dict[str, Any]:
        """
        Deploy model to endpoint.

        Args:
            name: Model name
            version: Model version
            endpoint: Deployment endpoint

        Returns:
            Deployment result
        """
        model = await self.get_model(name, version)

        if not model:
            return {"error": "Model not found"}

        logger.info(f"Deploying {name}:{version} to {endpoint}")

        return {
            "status": "success",
            "model": f"{name}:{version}",
            "endpoint": endpoint,
            "deployed_at": datetime.now().isoformat(),
        }

    async def archive(self, name: str, version: str) -> bool:
        """Archive old model version."""
        key = f"{name}:{version}"
        if key in self.models:
            self.models[key].status = "archived"
            logger.info(f"Archived model: {key}")
            return True
        return False

    async def get_performance_history(
        self,
        name: str,
    ) -> List[Dict[str, Any]]:
        """Get performance history for a model."""
        if name not in self.model_versions:
            return []

        history = []
        for model in self.model_versions[name]:
            history.append(
                {
                    "version": model.version,
                    "metrics": model.metrics,
                    "created_at": model.created_at.isoformat(),
                }
            )

        return history

    async def compare_models(
        self,
        name: str,
        versions: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Compare model versions."""
        if name not in self.model_versions:
            return {"error": "Model not found"}

        models = self.model_versions[name]
        if versions:
            models = [m for m in models if m.version in versions]

        comparison = {
            "model": name,
            "versions": [],
        }

        for model in models:
            comparison["versions"].append(
                {
                    "version": model.version,
                    "metrics": model.metrics,
                    "status": model.status,
                }
            )

        return comparison
