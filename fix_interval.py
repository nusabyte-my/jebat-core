"""Fix sqlalchemy.interval usage in models.py"""

import re

with open(
    r"C:\Users\shaid\Desktop\Dev\jebat\database\models.py", "r", encoding="utf-8"
) as f:
    content = f.read()

# Replace sqlalchemy.interval with interval
content = content.replace("sqlalchemy.interval", "interval")

with open(
    r"C:\Users\shaid\Desktop\Dev\jebat\database\models.py", "w", encoding="utf-8"
) as f:
    f.write(content)

print("Fixed sqlalchemy.interval usage in models.py")
