"""默写本生成 API 路由"""
from fastapi import APIRouter, Query, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
from typing import Optional

from ..services.dictation_service import DictationService


router = APIRouter(prefix="/api/dictation", tags=["dictation"])
dictation_service = DictationService()


class GenerateDictationRequest(BaseModel):
    """生成默写本请求模型"""
    user_id: Optional[str] = "default"
    top_n: Optional[int] = 50
    format: Optional[str] = "txt"


@router.post("/generate")
async def generate_dictation_book(
    user_id: str = Query("default", description="用户ID"),
    top_n: int = Query(50, description="单词数量（前N个高频错词）", ge=1, le=1000),
    format: str = Query("txt", description="文件格式（txt 或 pdf）")
):
    """生成默写本
    
    Args:
        user_id: 用户ID（默认为 default）
        top_n: 包含的单词数量（默认50，最大1000）
        format: 文件格式（txt 或 pdf，默认 txt）
        
    Returns:
        默写本文件内容
    """
    try:
        # 验证格式参数
        format_lower = format.lower()
        if format_lower not in ["txt", "pdf"]:
            raise HTTPException(
                status_code=400,
                detail={
                    "code": "INVALID_FORMAT",
                    "message": "文件格式必须是 txt 或 pdf",
                    "details": [{"field": "format", "message": "无效的格式参数"}]
                }
            )
        
        # 生成默写本
        file_content = dictation_service.generate_dictation_book(
            user_id=user_id,
            top_n=top_n,
            format=format_lower
        )
        
        # 设置响应头
        if format_lower == "pdf":
            media_type = "application/pdf"
            filename = f"dictation_book_{user_id}.pdf"
        else:
            media_type = "text/plain; charset=utf-8"
            filename = f"dictation_book_{user_id}.txt"
        
        # 返回文件
        return Response(
            content=file_content,
            media_type=media_type,
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "code": "DICTATION_ERROR",
                "message": f"生成默写本失败: {str(e)}",
                "details": []
            }
        )
