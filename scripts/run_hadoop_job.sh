#!/bin/bash
# run_hadoop_job.sh - 一键运行 Hadoop Streaming 错词分析作业

# ============================================
# 配置区域 - 根据你的环境修改
# ============================================
HADOOP_HOME=${HADOOP_HOME:-/usr/local/hadoop}
STREAMING_JAR=$(find $HADOOP_HOME -name "hadoop-streaming*.jar" 2>/dev/null | head -1)

# 脚本路径（相对于项目根目录）
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
MAPPER_PATH="$PROJECT_ROOT/mapreduce/mapper.py"
REDUCER_PATH="$PROJECT_ROOT/mapreduce/reducer.py"

# HDFS 路径
HDFS_INPUT_DIR=${HDFS_INPUT_DIR:-/user/wordmemory/input}
HDFS_OUTPUT_DIR=${HDFS_OUTPUT_DIR:-/user/wordmemory/output}

# 本地数据路径
LOCAL_DATA_DIR="$PROJECT_ROOT/data"

# ============================================
# 函数定义
# ============================================

print_header() {
    echo "=============================================="
    echo "  Hadoop Streaming 错词分析作业"
    echo "=============================================="
    echo "时间: $(date)"
    echo "HADOOP_HOME: $HADOOP_HOME"
    echo "STREAMING_JAR: $STREAMING_JAR"
    echo "MAPPER: $MAPPER_PATH"
    echo "REDUCER: $REDUCER_PATH"
    echo "HDFS INPUT: $HDFS_INPUT_DIR"
    echo "HDFS OUTPUT: $HDFS_OUTPUT_DIR"
    echo "=============================================="
}

check_prerequisites() {
    echo "[1/6] 检查前提条件..."
    
    # 检查 Hadoop
    if ! command -v hadoop &> /dev/null; then
        echo "错误: 找不到 hadoop 命令，请确保 HADOOP_HOME 已设置"
        exit 1
    fi
    echo "  ✓ Hadoop 命令可用"
    
    # 检查 Streaming JAR
    if [ -z "$STREAMING_JAR" ] || [ ! -f "$STREAMING_JAR" ]; then
        echo "错误: 找不到 Hadoop Streaming JAR"
        echo "请设置 HADOOP_HOME 环境变量或手动指定 STREAMING_JAR"
        exit 1
    fi
    echo "  ✓ Streaming JAR: $STREAMING_JAR"
    
    # 检查脚本文件
    if [ ! -f "$MAPPER_PATH" ]; then
        echo "错误: 找不到 Mapper 脚本: $MAPPER_PATH"
        exit 1
    fi
    echo "  ✓ Mapper 脚本存在"
    
    if [ ! -f "$REDUCER_PATH" ]; then
        echo "错误: 找不到 Reducer 脚本: $REDUCER_PATH"
        exit 1
    fi
    echo "  ✓ Reducer 脚本存在"
    
    # 检查 HDFS
    if ! hdfs dfs -ls / &> /dev/null; then
        echo "错误: 无法连接到 HDFS"
        exit 1
    fi
    echo "  ✓ HDFS 连接正常"
}

prepare_input_data() {
    echo ""
    echo "[2/6] 准备输入数据..."
    
    # 创建 HDFS 目录
    hdfs dfs -mkdir -p $HDFS_INPUT_DIR
    
    # 检查本地错词数据
    LOCAL_ERROR_FILE="$LOCAL_DATA_DIR/error_records.json"
    TEMP_INPUT_FILE="/tmp/mapreduce_input_$(date +%s).txt"
    
    if [ -f "$LOCAL_ERROR_FILE" ]; then
        echo "  从 $LOCAL_ERROR_FILE 提取数据..."
        
        # 使用 Python 转换 JSON 为 TSV 格式
        python3 << EOF
import json
import sys

try:
    with open('$LOCAL_ERROR_FILE', 'r', encoding='utf-8') as f:
        records = json.load(f)
    
    with open('$TEMP_INPUT_FILE', 'w', encoding='utf-8') as f:
        for record in records:
            line = f"{record['word_id']}\t{record['user_id']}\t{record['wrong_answer']}\t{record['timestamp']}\n"
            f.write(line)
    
    print(f"  ✓ 转换了 {len(records)} 条错词记录")
except Exception as e:
    print(f"  警告: 转换数据时出错: {e}")
    # 创建空文件
    open('$TEMP_INPUT_FILE', 'w').close()
EOF
    else
        echo "  警告: 找不到本地错词数据，创建示例数据..."
        cat > $TEMP_INPUT_FILE << 'SAMPLE'
sample_word1	user1	wrong1	2025-01-01T10:00:00
sample_word1	user1	wrong2	2025-01-01T10:05:00
sample_word2	user1	wrong3	2025-01-01T10:10:00
SAMPLE
    fi
    
    # 上传到 HDFS
    echo "  上传数据到 HDFS..."
    hdfs dfs -put -f $TEMP_INPUT_FILE $HDFS_INPUT_DIR/input.txt
    
    # 验证
    echo "  验证上传..."
    hdfs dfs -ls $HDFS_INPUT_DIR/
    
    # 清理临时文件
    rm -f $TEMP_INPUT_FILE
    
    echo "  ✓ 输入数据准备完成"
}

clean_output() {
    echo ""
    echo "[3/6] 清理旧的输出目录..."
    hdfs dfs -rm -r -f $HDFS_OUTPUT_DIR
    echo "  ✓ 输出目录已清理"
}

run_mapreduce() {
    echo ""
    echo "[4/6] 运行 MapReduce 作业..."
    echo ""
    
    JOB_NAME="WordMemory-ErrorAnalysis-$(date +%Y%m%d%H%M%S)"
    
    hadoop jar $STREAMING_JAR \
        -D mapreduce.job.name="$JOB_NAME" \
        -D mapreduce.job.reduces=1 \
        -D stream.num.map.output.key.fields=1 \
        -files $MAPPER_PATH,$REDUCER_PATH \
        -mapper "python3 mapper.py" \
        -reducer "python3 reducer.py" \
        -input $HDFS_INPUT_DIR/input.txt \
        -output $HDFS_OUTPUT_DIR
    
    if [ $? -ne 0 ]; then
        echo ""
        echo "错误: MapReduce 作业失败！"
        exit 1
    fi
    
    echo ""
    echo "  ✓ MapReduce 作业完成"
}

show_results() {
    echo ""
    echo "[5/6] 查看结果..."
    echo ""
    echo "=============================================="
    echo "  高频错词排行榜（按错误次数降序）"
    echo "=============================================="
    echo "单词ID                                  错误次数"
    echo "----------------------------------------------"
    hdfs dfs -cat $HDFS_OUTPUT_DIR/part-00000
    echo "=============================================="
}

download_results() {
    echo ""
    echo "[6/6] 下载结果到本地..."
    
    OUTPUT_FILE="$LOCAL_DATA_DIR/hadoop_analysis_result_$(date +%Y%m%d%H%M%S).txt"
    hdfs dfs -get $HDFS_OUTPUT_DIR/part-00000 $OUTPUT_FILE
    
    echo "  ✓ 结果已保存到: $OUTPUT_FILE"
}

# ============================================
# 主程序
# ============================================

main() {
    print_header
    check_prerequisites
    prepare_input_data
    clean_output
    run_mapreduce
    show_results
    download_results
    
    echo ""
    echo "=============================================="
    echo "  作业完成！"
    echo "=============================================="
}

# 运行主程序
main "$@"
