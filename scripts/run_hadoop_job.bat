@echo off
REM run_hadoop_job.bat - Windows 版 Hadoop Streaming 作业脚本
REM 注意：需要在安装了 Hadoop 的 Windows 环境或 WSL 中运行

echo ==============================================
echo   Hadoop Streaming 错词分析作业 (Windows)
echo ==============================================

REM 配置区域
set HADOOP_HOME=%HADOOP_HOME%
if "%HADOOP_HOME%"=="" (
    echo 错误: 请设置 HADOOP_HOME 环境变量
    exit /b 1
)

set HDFS_INPUT_DIR=/user/wordmemory/input
set HDFS_OUTPUT_DIR=/user/wordmemory/output

REM 获取脚本目录
set SCRIPT_DIR=%~dp0
set PROJECT_ROOT=%SCRIPT_DIR%..

echo HADOOP_HOME: %HADOOP_HOME%
echo PROJECT_ROOT: %PROJECT_ROOT%

REM 检查 Hadoop
echo.
echo [1/4] 检查 Hadoop 环境...
call hadoop version
if errorlevel 1 (
    echo 错误: Hadoop 命令不可用
    exit /b 1
)
echo √ Hadoop 可用

REM 准备数据
echo.
echo [2/4] 准备输入数据...
call hdfs dfs -mkdir -p %HDFS_INPUT_DIR%

REM 转换数据（使用 Python）
python -c "import json; records = json.load(open('%PROJECT_ROOT%/data/error_records.json', encoding='utf-8')); f = open('temp_input.txt', 'w', encoding='utf-8'); [f.write(f\"{r['word_id']}\t{r['user_id']}\t{r['wrong_answer']}\t{r['timestamp']}\n\") for r in records]; f.close(); print(f'转换了 {len(records)} 条记录')"

call hdfs dfs -put -f temp_input.txt %HDFS_INPUT_DIR%/input.txt
del temp_input.txt
echo √ 数据已上传

REM 清理输出
echo.
echo [3/4] 清理旧输出...
call hdfs dfs -rm -r -f %HDFS_OUTPUT_DIR%

REM 运行作业
echo.
echo [4/4] 运行 MapReduce 作业...

REM 查找 Streaming JAR
for /f "delims=" %%i in ('dir /s /b "%HADOOP_HOME%\share\hadoop\tools\lib\hadoop-streaming*.jar" 2^>nul') do set STREAMING_JAR=%%i

if "%STREAMING_JAR%"=="" (
    echo 错误: 找不到 Hadoop Streaming JAR
    exit /b 1
)

echo 使用 JAR: %STREAMING_JAR%

call hadoop jar %STREAMING_JAR% ^
    -D mapreduce.job.name="WordMemory-ErrorAnalysis" ^
    -files %PROJECT_ROOT%/mapreduce/mapper.py,%PROJECT_ROOT%/mapreduce/reducer.py ^
    -mapper "python mapper.py" ^
    -reducer "python reducer.py" ^
    -input %HDFS_INPUT_DIR%/input.txt ^
    -output %HDFS_OUTPUT_DIR%

if errorlevel 1 (
    echo 错误: MapReduce 作业失败
    exit /b 1
)

REM 显示结果
echo.
echo ==============================================
echo   结果：
echo ==============================================
call hdfs dfs -cat %HDFS_OUTPUT_DIR%/part-00000

REM 下载结果
call hdfs dfs -get %HDFS_OUTPUT_DIR%/part-00000 %PROJECT_ROOT%/data/hadoop_result.txt
echo.
echo √ 结果已保存到: %PROJECT_ROOT%/data/hadoop_result.txt

echo.
echo ==============================================
echo   作业完成！
echo ==============================================
