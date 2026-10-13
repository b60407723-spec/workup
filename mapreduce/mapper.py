#!/usr/bin/env python3
"""
Mapper 脚本：读取错词记录，输出 (word_id, 1) 键值对
输入格式：word_id\tuser_id\twrong_answer\ttimestamp
输出格式：word_id\t1
"""
import sys


def mapper():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        
        try:
            fields = line.split('\t')
            if len(fields) >= 1:
                word_id = fields[0]
                print(f"{word_id}\t1")
        except Exception as e:
            # 记录错误但继续处理
            sys.stderr.write(f"Error processing line: {line}\n")
            sys.stderr.write(f"Error: {str(e)}\n")
            continue


if __name__ == "__main__":
    mapper()
