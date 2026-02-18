"""Fix sentinel.py import paths"""

with open(
    r"C:\Users\shaid\Desktop\Dev\jebat\features\sentinel\sentinel.py",
    "r",
    encoding="utf-8",
) as f:
    content = f.read()

# Fix relative imports to absolute
content = content.replace(
    "from ..database.repositories import", "from jebat.database.repositories import"
)
content = content.replace(
    "from ..database.models import", "from jebat.database.models import"
)
content = content.replace(
    "from ..decision_engine.engine import", "from jebat.core.decision.engine import"
)
content = content.replace(
    "from ..error_recovery.system import", "from jebat.error_recovery.system import"
)
content = content.replace(
    "from ..cache.cache_manager import", "from jebat.core.cache.smart_cache import"
)
content = content.replace(
    "from ..skills.base_skill import", "from jebat.skills.base_skill import"
)

with open(
    r"C:\Users\shaid\Desktop\Dev\jebat\features\sentinel\sentinel.py",
    "w",
    encoding="utf-8",
) as f:
    f.write(content)

print("Fixed sentinel.py import paths")
