import re


tag_pattern = re.compile(r"#([\w\u4e00-\u9fff]+)")


def extract_tags(text: str) -> list[str]:
    """从标题和描述中提取 #标签，去重后按首次出现顺序返回。"""
    seen: set[str] = set()
    tags: list[str] = []
    for match in tag_pattern.findall(text):
        tag = match.strip()
        if tag and tag not in seen:
            seen.add(tag)
            tags.append(tag)
    return tags
