def format_bug_report(data):
    return f"""
Summary: {data.get("summary")}
Affected Pages: {data.get("pages")}
Steps to Reproduce: {data.get("steps")}
Templates/Components: {data.get("components", "N/A")}
""".strip()
