#!/usr/bin/env python3
"""
本地测试脚本：模拟 MapReduce 流程
"""
import subprocess
import sys
from pathlib import Path


def run_local_mapreduce(input_file: str, output_file: str):
    """运行本地 MapReduce 测试"""
    script_dir = Path(__file__).parent
    mapper_path = script_dir / "mapper.py"
    reducer_path = script_dir / "reducer.py"
    
    try:
        # 步骤 1: 运行 Mapper
        with open(input_file, 'r') as f:
            mapper_process = subprocess.Popen(
                [sys.executable, str(mapper_path)],
                stdin=f,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            mapper_output, mapper_errors = mapper_process.communicate()
        
        if mapper_errors:
            print(f"Mapper errors: {mapper_errors}", file=sys.stderr)
        
        # 步骤 2: 排序 Mapper 输出
        sorted_output = '\n'.join(sorted(mapper_output.strip().split('\n')))
        
        # 步骤 3: 运行 Reducer
        reducer_process = subprocess.Popen(
            [sys.executable, str(reducer_path)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        reducer_output, reducer_errors = reducer_process.communicate(input=sorted_output)
        
        if reducer_errors:
            print(f"Reducer errors: {reducer_errors}", file=sys.stderr)
        
        # 步骤 4: 写入输出文件
        with open(output_file, 'w') as f:
            f.write(reducer_output)
        
        print(f"MapReduce 测试完成。结果已写入 {output_file}")
        return True
        
    except Exception as e:
        print(f"Error running MapReduce: {str(e)}", file=sys.stderr)
        return False


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python test_mapreduce.py <input_file> <output_file>")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    
    success = run_local_mapreduce(input_file, output_file)
    sys.exit(0 if success else 1)
