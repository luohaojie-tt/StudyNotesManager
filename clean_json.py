#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import re
import json

def clean_file():
    # 读取文件
    with open('系统架构设计文档.md', 'r', encoding='utf-8') as f:
        content = f.read()

    # 尝试解析为JSON数组
    try:
        data = json.loads(content)
        if isinstance(data, list) and len(data) > 0:
            # 提取所有text字段
            markdown_text = '\n'.join([item.get('text', '') for item in data if item.get('type') == 'text'])

            # 写回文件
            with open('系统架构设计文档.md', 'w', encoding='utf-8') as f:
                f.write(markdown_text)
            print('Success: File cleaned (JSON array format)')
            return
    except json.JSONDecodeError:
        pass

    # 尝试正则提取
    match = re.search(r'"text": "([\s\S]+?)", "files":', content)
    if not match:
        match = re.search(r'"text": "([\s\S]+?)"\s*\]\s*\}', content)

    if match:
        json_text = match.group(1)

        # 处理转义字符
        json_text = json_text.replace('\\n', '\n')
        json_text = json_text.replace('\\r', '\r')
        json_text = json_text.replace('\\t', '\t')
        json_text = json_text.replace('\\"', '"')

        # 写回文件
        with open('系统架构设计文档.md', 'w', encoding='utf-8') as f:
            f.write(json_text)
        print('Success: File cleaned (regex extraction)')
    else:
        print('Error: Could not extract markdown content')

if __name__ == '__main__':
    clean_file()
