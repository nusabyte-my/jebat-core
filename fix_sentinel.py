"""Fix sentinel.py truncated file"""

with open(
    r"C:\Users\shaid\Desktop\Dev\jebat\features\sentinel\sentinel.py",
    "r",
    encoding="utf-8",
) as f:
    content = f.read()

# Find and fix the truncated part
if 'SkillCapability(\n            name="policy_en' in content:
    content = content.replace(
        'SkillCapability(\n            name="policy_en',
        "    ]\n\n\n# End of Sentinel class",
    )
    with open(
        r"C:\Users\shaid\Desktop\Dev\jebat\features\sentinel\sentinel.py",
        "w",
        encoding="utf-8",
    ) as f:
        f.write(content)
    print("Fixed truncated sentinel.py")
else:
    print("No truncation found")
