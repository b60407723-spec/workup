"""单词管理 API 路由"""
from fastapi import APIRouter, HTTPException, UploadFile, File, Query
from pydantic import BaseModel, Field
from typing import Optional, List
import tempfile
import os

from ..services.word_service import WordService
from ..services.statistics_service import StatisticsService
from ..models import Word


router = APIRouter(prefix="/api/words", tags=["words"])
word_service = WordService()
stats_service = StatisticsService()


class WordInput(BaseModel):
    """添加单词的输入模型"""
    word: str = Field(..., description="英文单词")
    definition: str = Field(..., description="中文释义")
    part_of_speech: str = Field(..., description="词性")
    difficulty: Optional[int] = Field(1, ge=1, le=5, description="难度等级 (1-5)")


class WordResponse(BaseModel):
    """单词响应模型"""
    id: str
    word: str
    definition: str
    part_of_speech: str
    difficulty: int
    created_at: str
    updated_at: str


class ImportResponse(BaseModel):
    """导入响应模型"""
    success_count: int
    failed_count: int
    failed_lines: List[dict]
    total_lines: int


class ErrorResponse(BaseModel):
    """错误响应模型"""
    error: dict


@router.post("", response_model=WordResponse, status_code=201)
async def add_word(word_input: WordInput):
    """添加新单词
    
    Args:
        word_input: 单词输入数据
        
    Returns:
        创建的单词对象
        
    Raises:
        HTTPException: 400 - 验证失败或单词已存在
    """
    word_data = word_input.model_dump()
    word, error = word_service.add_word(word_data)
    
    if error:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "VALIDATION_ERROR",
                "message": error,
                "details": []
            }
        )
    
    stats_service.refresh_system_metrics()
    
    return WordResponse(
        id=word.id,
        word=word.word,
        definition=word.definition,
        part_of_speech=word.part_of_speech,
        difficulty=word.difficulty,
        created_at=word.created_at.isoformat(),
        updated_at=word.updated_at.isoformat()
    )


@router.get("", response_model=List[WordResponse])
async def get_words(
    difficulty: Optional[int] = Query(None, ge=1, le=5, description="按难度过滤"),
    part_of_speech: Optional[str] = Query(None, description="按词性过滤")
):
    """获取单词列表
    
    Args:
        difficulty: 难度等级过滤（可选）
        part_of_speech: 词性过滤（可选）
        
    Returns:
        单词列表
    """
    filter_params = {}
    if difficulty is not None:
        filter_params['difficulty'] = difficulty
    if part_of_speech is not None:
        filter_params['part_of_speech'] = part_of_speech
    
    words = word_service.get_words(filter_params)
    
    return [
        WordResponse(
            id=word.id,
            word=word.word,
            definition=word.definition,
            part_of_speech=word.part_of_speech,
            difficulty=word.difficulty,
            created_at=word.created_at.isoformat(),
            updated_at=word.updated_at.isoformat()
        )
        for word in words
    ]


@router.post("/import", response_model=ImportResponse)
async def import_words(file: UploadFile = File(...)):
    """批量导入单词
    
    Args:
        file: TXT 文件，每行格式：word\tdefinition\tpart_of_speech\tdifficulty
        
    Returns:
        导入结果
        
    Raises:
        HTTPException: 400 - 文件格式错误
    """
    # 验证文件类型
    if not file.filename.endswith('.txt'):
        raise HTTPException(
            status_code=400,
            detail={
                "code": "INVALID_FILE_TYPE",
                "message": "只支持 TXT 文件格式",
                "details": []
            }
        )
    
    # 保存上传的文件到临时位置
    try:
        with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.txt') as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        # 调用服务层处理导入
        result = word_service.import_words_from_file(temp_file_path)
        
        # 删除临时文件
        os.unlink(temp_file_path)
        
        stats_service.refresh_system_metrics()
        
        return ImportResponse(
            success_count=result.success_count,
            failed_count=result.failed_count,
            failed_lines=result.failed_lines,
            total_lines=result.total_lines
        )
    
    except Exception as e:
        # 确保临时文件被删除
        if 'temp_file_path' in locals() and os.path.exists(temp_file_path):
            os.unlink(temp_file_path)
        
        raise HTTPException(
            status_code=500,
            detail={
                "code": "IMPORT_ERROR",
                "message": f"导入过程中发生错误: {str(e)}",
                "details": []
            }
        )


@router.put("/{word_id}/master", status_code=200)
async def mark_word_as_mastered(
    word_id: str,
    user_id: str = Query("default_user", description="用户ID")
):
    """标记单词为已掌握
    
    Args:
        word_id: 单词ID
        user_id: 用户ID（默认为 default_user）
        
    Returns:
        成功消息
        
    Raises:
        HTTPException: 404 - 单词不存在
    """
    success, error = word_service.mark_as_mastered(word_id, user_id)
    
    if not success:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "WORD_NOT_FOUND",
                "message": error,
                "details": []
            }
        )
    
    stats_service.refresh_system_metrics()
    
    return {
        "message": "单词已标记为已掌握",
        "word_id": word_id,
        "user_id": user_id
    }
