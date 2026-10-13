"""全局错误处理中间件"""
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import logging
import traceback

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ErrorResponse:
    """标准化错误响应格式"""
    
    @staticmethod
    def format_error(code: str, message: str, details: list = None, status_code: int = 400):
        """格式化错误响应
        
        Args:
            code: 错误代码
            message: 错误消息
            details: 详细错误信息列表
            status_code: HTTP 状态码
            
        Returns:
            JSONResponse: 格式化的错误响应
        """
        return JSONResponse(
            status_code=status_code,
            content={
                "error": {
                    "code": code,
                    "message": message,
                    "details": details or []
                }
            }
        )


async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """处理 HTTP 异常
    
    Args:
        request: 请求对象
        exc: HTTP 异常
        
    Returns:
        JSONResponse: 格式化的错误响应
    """
    logger.warning(f"HTTP Exception: {exc.status_code} - {exc.detail}")
    
    # 如果 detail 已经是字典格式（来自我们的路由），直接返回
    if isinstance(exc.detail, dict):
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": exc.detail}
        )
    
    # 否则格式化为标准错误响应
    error_code_map = {
        400: "BAD_REQUEST",
        401: "UNAUTHORIZED",
        403: "FORBIDDEN",
        404: "NOT_FOUND",
        405: "METHOD_NOT_ALLOWED",
        409: "CONFLICT",
        422: "UNPROCESSABLE_ENTITY",
        500: "INTERNAL_SERVER_ERROR",
        503: "SERVICE_UNAVAILABLE"
    }
    
    code = error_code_map.get(exc.status_code, "HTTP_ERROR")
    
    return ErrorResponse.format_error(
        code=code,
        message=str(exc.detail),
        status_code=exc.status_code
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """处理请求验证异常
    
    Args:
        request: 请求对象
        exc: 验证异常
        
    Returns:
        JSONResponse: 格式化的错误响应
    """
    logger.warning(f"Validation Error: {exc.errors()}")
    
    # 格式化验证错误详情
    details = []
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error["loc"] if loc != "body")
        details.append({
            "field": field,
            "message": error["msg"],
            "type": error["type"]
        })
    
    return ErrorResponse.format_error(
        code="VALIDATION_ERROR",
        message="输入数据验证失败",
        details=details,
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY
    )


async def general_exception_handler(request: Request, exc: Exception):
    """处理未捕获的异常
    
    Args:
        request: 请求对象
        exc: 异常对象
        
    Returns:
        JSONResponse: 格式化的错误响应
    """
    # 记录完整的错误堆栈
    logger.error(f"Unhandled Exception: {str(exc)}")
    logger.error(traceback.format_exc())
    
    return ErrorResponse.format_error(
        code="INTERNAL_SERVER_ERROR",
        message="服务器内部错误，请稍后重试",
        details=[{"error": str(exc)}],
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
    )


async def request_logging_middleware(request: Request, call_next):
    """请求日志中间件
    
    Args:
        request: 请求对象
        call_next: 下一个中间件或路由处理器
        
    Returns:
        Response: 响应对象
    """
    # 记录请求信息
    logger.info(f"Request: {request.method} {request.url.path}")
    
    try:
        response = await call_next(request)
        
        # 记录响应状态
        logger.info(f"Response: {response.status_code}")
        
        return response
    except Exception as e:
        logger.error(f"Request failed: {str(e)}")
        raise
