"""Fix metadata reserved word in models.py"""

import re

with open(
    r"C:\Users\shaid\Desktop\Dev\jebat\database\models.py", "r", encoding="utf-8"
) as f:
    content = f.read()

# Replace metadata with custom_metadata (but not in comments or strings)
content = re.sub(r"\bmetadata:\s*Mapped\[Dict", "custom_metadata: Mapped[Dict", content)
content = re.sub(r"\bmetadata\.value\b", "custom_metadata.value", content)
content = re.sub(r'\bmetadata\["', 'custom_metadata["', content)

with open(
    r"C:\Users\shaid\Desktop\Dev\jebat\database\models.py", "w", encoding="utf-8"
) as f:
    f.write(content)

print("Fixed metadata reserved word in models.py")
