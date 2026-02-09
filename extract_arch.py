#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
import sys

# 读取原始JSON文件
json_file = r"C:\Users\lhj\.claude\projects\D--work-StudyNotesManager\2d588a7c-2755-4042-853c-22c174376225\tool-results\call_10c7d62cb5574bd0993c4b03.json"

with open(json_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

# 提取所有text字段并连接
markdown_parts = []
for item in data:
    if item.get('type') == 'text':
        markdown_parts.append(item['text'])

markdown_text = '\n'.join(markdown_parts)

# 写入新的markdown文件
output_file = r"D:\work\StudyNotesManager\系统架构设计文档.md"
with open(output_file, 'w', encoding='utf-8') as f:
    f.write(markdown_text)

print("Success: Architecture design document saved")
print(f"Total length: {len(markdown_text)} characters")
