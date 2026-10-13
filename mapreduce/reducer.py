#!/usr/bin/env python3
"""
Reducer 脚本：聚合相同单词的错误次数，输出排序结果
输入格式：word_id\t1 (已按 key 排序)
输出格式：word_id\tcount
"""
import sys


def reducer():
    current_word = None
    current_count = 0
    results = []
    
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        
        try:
            word, count = line.split('\t')
            count = int(count)
            
            if word == current_word:
                current_count += count
            else:
                if current_word:
                    results.append((current_word, current_count))
                current_word = word
                current_count = count
        except Exception as e:
            sys.stderr.write(f"Error processing line: {line}\n")
            sys.stderr.write(f"Error: {str(e)}\n")
            continue
    
    # 输出最后一个单词
    if current_word:
        results.append((current_word, current_count))
    
    # 按错误次数降序排序
    results.sort(key=lambda x: x[1], reverse=True)
    
    # 输出结果
    for word, count in results:
        print(f"{word}\t{count}")


if __name__ == "__main__":
    reducer()
