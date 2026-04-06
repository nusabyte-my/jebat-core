"""Fix sentinel.py missing module imports"""

with open(
    r"C:\Users\shaid\Desktop\Dev\jebat\features\sentinel\sentinel.py",
    "r",
    encoding="utf-8",
) as f:
    content = f.read()

# Replace the problematic imports with optional imports
old_imports = """from jebat.database.repositories import SecurityEventRepository, SecurityPolicyRepository, AuditLogRepository, UserRepository
from jebat.database.models import SecurityEvent, SecurityPolicy, AuditLog, User
from jebat.core.decision.engine import DecisionEngine
from jebat.error_recovery.system import ErrorRecoverySystem
from jebat.core.cache.smart_cache import CacheManager
from jebat.skills.base_skill import BaseSkill, SkillResult, SkillParameter, SkillCapability"""

new_imports = """from jebat.database.repositories import SecurityEventRepository, SecurityPolicyRepository, AuditLogRepository, UserRepository
from jebat.database.models import SecurityEvent, SecurityPolicy, AuditLog, User
from jebat.core.decision.engine import DecisionEngine
try:
    from jebat.error_recovery.system import ErrorRecoverySystem
except ImportError:
    ErrorRecoverySystem = None
from jebat.core.cache.smart_cache import CacheManager
from jebat.skills.base_skill import BaseSkill, SkillResult, SkillParameter, SkillCapability"""

content = content.replace(old_imports, new_imports)

with open(
    r"C:\Users\shaid\Desktop\Dev\jebat\features\sentinel\sentinel.py",
    "w",
    encoding="utf-8",
) as f:
    f.write(content)

print("Fixed sentinel.py optional imports")
