"""测试 API 路由"""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Optional

from ..services.test_service import TestService
from ..services.statistics_service import StatisticsService
from ..models import Word


router = APIRouter(prefix="/api/test", tags=["test"])
test_service = TestService()
stats_service = StatisticsService()


class StartTestRequest(BaseModel):
    """开始测试请求模型"""
    user_id: str = Field(..., description="用户ID")
    word_count: int = Field(..., ge=1, description="测试单词数量")


class StartTestResponse(BaseModel):
    """开始测试响应模型"""
    session_id: str
    user_id: str
    word_count: int
    words: List[dict]
    start_time: str


class SubmitAnswerRequest(BaseModel):
    """提交答案请求模型"""
    session_id: str = Field(..., description="测试会话ID")
    word_id: str = Field(..., description="单词ID")
    user_answer: str = Field(..., description="用户答案")


class SubmitAnswerResponse(BaseModel):
    """提交答案响应模型"""
    is_correct: bool
    word_id: str
    correct_answer: Optional[str] = None


class EndTestRequest(BaseModel):
    """结束测试请求模型"""
    session_id: str = Field(..., description="测试会话ID")


class TestResultResponse(BaseModel):
    """测试结果响应模型"""
    session_id: str
    total_count: int
    correct_count: int
    wrong_count: int
    accuracy: float
    duration: int
    timestamp: str


@router.post("/start", response_model=StartTestResponse, status_code=201)
async def start_test(request: StartTestRequest):
    """开始测试
    
    根据需求 2.1：随机选择单词并显示中文释义，要求用户输入英文单词
    
    Args:
        request: 开始测试请求
        
    Returns:
        测试会话信息和单词列表
        
    Raises:
        HTTPException: 400 - 参数无效或已有进行中的测试
    """
    try:
        # 创建测试会话
        session = test_service.start_test(request.user_id, request.word_count)
        
        stats_service.refresh_system_metrics()
        
        # 获取测试单词列表
        words = test_service.get_session_words(session.id)
        
        # 构建响应（只返回中文释义，不返回英文单词）
        word_list = [
            {
                "word_id": word.id,
                "definition": word.definition,
                "part_of_speech": word.part_of_speech,
                "difficulty": word.difficulty
            }
            for word in words
        ]
        
        return StartTestResponse(
            session_id=session.id,
            user_id=session.user_id,
            word_count=len(session.word_ids),
            words=word_list,
            start_time=session.start_time.isoformat()
        )
    
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "VALIDATION_ERROR",
                "message": str(e),
                "details": []
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "code": "INTERNAL_ERROR",
                "message": f"启动测试时发生错误: {str(e)}",
                "details": []
            }
        )


@router.post("/submit", response_model=SubmitAnswerResponse)
async def submit_answer(request: SubmitAnswerRequest):
    """提交答案
    
    根据需求 2.2：验证答案正确性并提供即时反馈
    根据需求 2.3：如果答案错误，记录错词信息
    
    Args:
        request: 提交答案请求
        
    Returns:
        答案验证结果
        
    Raises:
        HTTPException: 400 - 会话不存在或单词不在测试中
    """
    try:
        # 验证答案
        is_correct = test_service.submit_answer(
            request.session_id,
            request.word_id,
            request.user_answer
        )
        
        # 如果答案错误，返回正确答案
        correct_answer = None
        if not is_correct:
            # 获取单词信息
            from ..repositories.word_repository import WordRepository
            word_repo = WordRepository()
            word = word_repo.find_by_id(request.word_id)
            if word:
                correct_answer = word.word
        
        return SubmitAnswerResponse(
            is_correct=is_correct,
            word_id=request.word_id,
            correct_answer=correct_answer
        )
    
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "VALIDATION_ERROR",
                "message": str(e),
                "details": []
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "code": "INTERNAL_ERROR",
                "message": f"提交答案时发生错误: {str(e)}",
                "details": []
            }
        )


@router.post("/end", response_model=TestResultResponse)
async def end_test(request: EndTestRequest):
    """结束测试
    
    根据需求 2.4：显示测试结果统计，包括正确率、错误数量和用时
    
    Args:
        request: 结束测试请求
        
    Returns:
        测试结果统计
        
    Raises:
        HTTPException: 400 - 会话不存在或已结束
    """
    try:
        # 结束测试并获取结果
        result = test_service.end_test(request.session_id)
        
        return TestResultResponse(
            session_id=result.session_id,
            total_count=result.total_count,
            correct_count=result.correct_count,
            wrong_count=result.wrong_count,
            accuracy=result.accuracy,
            duration=result.duration,
            timestamp=result.timestamp.isoformat()
        )
    
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "VALIDATION_ERROR",
                "message": str(e),
                "details": []
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "code": "INTERNAL_ERROR",
                "message": f"结束测试时发生错误: {str(e)}",
                "details": []
            }
        )


@router.get("/results/{session_id}", response_model=TestResultResponse)
async def get_test_results(session_id: str):
    """获取测试结果
    
    根据需求 2.4：获取已完成测试的结果统计
    
    Args:
        session_id: 测试会话ID
        
    Returns:
        测试结果统计
        
    Raises:
        HTTPException: 404 - 会话不存在
        HTTPException: 400 - 测试未完成
    """
    try:
        # 获取测试会话
        session = test_service.get_test_session(session_id)
        
        if not session:
            raise HTTPException(
                status_code=404,
                detail={
                    "code": "SESSION_NOT_FOUND",
                    "message": "测试会话不存在",
                    "details": []
                }
            )
        
        if session.status != 'completed':
            raise HTTPException(
                status_code=400,
                detail={
                    "code": "TEST_NOT_COMPLETED",
                    "message": "测试尚未完成",
                    "details": []
                }
            )
        
        # 计算测试结果
        result = test_service._calculate_test_result(session)
        
        return TestResultResponse(
            session_id=result.session_id,
            total_count=result.total_count,
            correct_count=result.correct_count,
            wrong_count=result.wrong_count,
            accuracy=result.accuracy,
            duration=result.duration,
            timestamp=result.timestamp.isoformat()
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "code": "INTERNAL_ERROR",
                "message": f"获取测试结果时发生错误: {str(e)}",
                "details": []
            }
        )
