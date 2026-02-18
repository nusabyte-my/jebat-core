"""Fix interval expressions in models.py"""

with open(
    r"C:\Users\shaid\Desktop\Dev\jebat\database\models.py", "r", encoding="utf-8"
) as f:
    content = f.read()

# Replace func.cast interval expressions with text() expressions
content = content.replace(
    'func.cast("5 minutes", interval)', "text(\"NOW() + INTERVAL '5 minutes'\")"
)
content = content.replace(
    'func.cast("24 hours", interval)', "text(\"NOW() + INTERVAL '24 hours'\")"
)
content = content.replace(
    'func.cast("7 days", interval)', "text(\"NOW() + INTERVAL '7 days'\")"
)
content = content.replace(
    'func.cast("90 days", interval)', "text(\"NOW() + INTERVAL '90 days'\")"
)

with open(
    r"C:\Users\shaid\Desktop\Dev\jebat\database\models.py", "w", encoding="utf-8"
) as f:
    f.write(content)

print("Fixed interval expressions in models.py")
