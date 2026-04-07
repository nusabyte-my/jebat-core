"""
🧠 JEBAT ML Skills - Machine Learning Integration

Machine learning capabilities for JEBAT platform:
- AutoML integration
- Pre-trained models
- Classification, Regression, Clustering
- NLP tasks
- Model deployment

Part of Q2 2026 Roadmap
"""

from .auto_ml import AutoML
from .ml_classifier import MLClassifier
from .ml_cluster import MLClusterer
from .ml_nlp import MLNLP
from .ml_regressor import MLRegressor
from .model_registry import ModelRegistry

__all__ = [
    "MLClassifier",
    "MLRegressor",
    "MLClusterer",
    "MLNLP",
    "AutoML",
    "ModelRegistry",
]
