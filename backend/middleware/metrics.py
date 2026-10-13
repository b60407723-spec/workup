"""Prometheus 监控指标中间件"""
import time
from prometheus_client import Counter, Histogram, Gauge, Info, generate_latest, CONTENT_TYPE_LATEST
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Callable

# ============================================
# 定义 Prometheus 指标
# ============================================

# 请求计数器
REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status_code']
)

# 请求延迟直方图
REQUEST_LATENCY = Histogram(
    'http_request_duration_seconds',
    'HTTP request latency in seconds',
    ['method', 'endpoint'],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
)

# MapReduce 作业指标
MAPREDUCE_JOBS_TOTAL = Counter(
    'mapreduce_jobs_total',
    'Total MapReduce jobs',
    ['status', 'mode']  # status: success/failed, mode: local/hadoop
)

MAPREDUCE_JOB_DURATION = Histogram(
    'mapreduce_job_duration_seconds',
    'MapReduce job duration in seconds',
    ['mode'],
    buckets=[1.0, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0, 600.0]
)

MAPREDUCE_JOBS_IN_PROGRESS = Gauge(
    'mapreduce_jobs_in_progress',
    'Number of MapReduce jobs currently running'
)

# 错词分析吞吐量
ERROR_RECORDS_PROCESSED = Counter(
    'error_records_processed_total',
    'Total error records processed by MapReduce'
)

ERROR_ANALYSIS_THROUGHPUT = Gauge(
    'error_analysis_throughput_per_second',
    'Error records processed per second'
)

# HDFS IO 指标
HDFS_BYTES_READ = Counter(
    'hdfs_bytes_read_total',
    'Total bytes read from HDFS'
)

HDFS_BYTES_WRITTEN = Counter(
    'hdfs_bytes_written_total',
    'Total bytes written to HDFS'
)

HDFS_OPERATIONS = Counter(
    'hdfs_operations_total',
    'Total HDFS operations',
    ['operation']  # put, get, delete, mkdir
)

# 单词测试指标
TEST_SESSIONS_TOTAL = Counter(
    'test_sessions_total',
    'Total test sessions',
    ['status']  # completed, cancelled
)

TEST_ANSWERS_TOTAL = Counter(
    'test_answers_total',
    'Total test answers',
    ['result']  # correct, incorrect
)

# 系统信息
SYSTEM_INFO = Info(
    'word_memory_system',
    'Word Memory System information'
)

# 活跃用户数
ACTIVE_USERS = Gauge(
    'active_users',
    'Number of active users'
)

# 单词总数
TOTAL_WORDS = Gauge(
    'total_words',
    'Total number of words in the system'
)


# ============================================
# 中间件类
# ============================================

class PrometheusMiddleware(BaseHTTPMiddleware):
    """Prometheus 监控中间件"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 跳过 metrics 端点本身
        if request.url.path == "/metrics":
            return await call_next(request)
        
        # 记录开始时间
        start_time = time.time()
        
        # 处理请求
        response = await call_next(request)
        
        # 计算延迟
        latency = time.time() - start_time
        
        # 获取端点路径（简化）
        endpoint = self._get_endpoint(request.url.path)
        
        # 记录指标
        REQUEST_COUNT.labels(
            method=request.method,
            endpoint=endpoint,
            status_code=response.status_code
        ).inc()
        
        REQUEST_LATENCY.labels(
            method=request.method,
            endpoint=endpoint
        ).observe(latency)
        
        return response
    
    def _get_endpoint(self, path: str) -> str:
        """简化端点路径，避免高基数"""
        # 将动态路径参数替换为占位符
        parts = path.split('/')
        simplified = []
        for part in parts:
            if part and (len(part) > 30 or '-' in part and len(part) > 10):
                # 可能是 UUID 或其他动态参数
                simplified.append('{id}')
            else:
                simplified.append(part)
        return '/'.join(simplified)


# ============================================
# 辅助函数
# ============================================

def record_mapreduce_job(mode: str, status: str, duration: float, records_count: int):
    """记录 MapReduce 作业指标"""
    MAPREDUCE_JOBS_TOTAL.labels(status=status, mode=mode).inc()
    MAPREDUCE_JOB_DURATION.labels(mode=mode).observe(duration)
    ERROR_RECORDS_PROCESSED.inc(records_count)
    
    if duration > 0:
        ERROR_ANALYSIS_THROUGHPUT.set(records_count / duration)


def record_hdfs_operation(operation: str, bytes_count: int = 0):
    """记录 HDFS 操作指标"""
    HDFS_OPERATIONS.labels(operation=operation).inc()
    
    if operation == 'get':
        HDFS_BYTES_READ.inc(bytes_count)
    elif operation == 'put':
        HDFS_BYTES_WRITTEN.inc(bytes_count)


def record_test_session(status: str):
    """记录测试会话指标"""
    TEST_SESSIONS_TOTAL.labels(status=status).inc()


def record_test_answer(is_correct: bool):
    """记录测试答案指标"""
    result = 'correct' if is_correct else 'incorrect'
    TEST_ANSWERS_TOTAL.labels(result=result).inc()


def update_system_metrics(total_words: int, active_users: int):
    """更新系统指标"""
    TOTAL_WORDS.set(total_words)
    ACTIVE_USERS.set(active_users)


def set_system_info(version: str, mode: str):
    """设置系统信息"""
    SYSTEM_INFO.info({
        'version': version,
        'mapreduce_mode': mode
    })


def increment_jobs_in_progress():
    """增加进行中的作业数"""
    MAPREDUCE_JOBS_IN_PROGRESS.inc()


def decrement_jobs_in_progress():
    """减少进行中的作业数"""
    MAPREDUCE_JOBS_IN_PROGRESS.dec()
