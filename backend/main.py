from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.responses import JSONResponse
import logging
import os

from .routes.word_routes import router as word_router
from .routes.test_routes import router as test_router
from .routes.review_routes import router as review_router
from .routes.stats_routes import router as stats_router
from .routes.mapreduce_routes import router as mapreduce_router
from .routes.dictation_routes import router as dictation_router
from .routes.metrics_routes import router as metrics_router
from .middleware.error_handler import (
    http_exception_handler,
    validation_exception_handler,
    general_exception_handler,
    request_logging_middleware
)
from .middleware.metrics import PrometheusMiddleware, set_system_info
from .services.mapreduce_service import MapReduceService
from .services.statistics_service import StatisticsService

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 创建 FastAPI 应用
app = FastAPI(
    title="英语单词记忆系统",
    description="基于 Hadoop MapReduce 的智能英语单词学习平台",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# 配置 CORS - 允许前端访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应该指定具体的域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 添加请求日志中间件
app.middleware("http")(request_logging_middleware)

# 添加 Prometheus 监控中间件（采集请求数、延迟等指标）
app.add_middleware(PrometheusMiddleware)

# 注册全局异常处理器
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# 注册路由
app.include_router(word_router)
app.include_router(test_router)
app.include_router(review_router)
app.include_router(stats_router)
app.include_router(mapreduce_router)
app.include_router(dictation_router)
app.include_router(metrics_router)


@app.get("/")
async def root():
    """API 根路径"""
    return {
        "message": "英语单词记忆系统 API",
        "version": "1.0.0",
        "docs": "/api/docs",
        "health": "/health"
    }


@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {
        "status": "healthy",
        "service": "英语单词记忆系统",
        "version": "1.0.0"
    }


@app.on_event("startup")
async def startup_event():
    """应用启动事件"""
    set_system_info(app.version, MapReduceService.RUN_MODE)
    StatisticsService().refresh_system_metrics()
    logger.info("英语单词记忆系统启动成功")
    logger.info("API 文档: http://localhost:8000/api/docs")
    logger.info("MapReduce 运行模式: %s", MapReduceService.RUN_MODE)


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭事件"""
    logger.info("英语单词记忆系统正在关闭...")
