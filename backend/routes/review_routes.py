"""复习相关的 API 路由"""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional
from ..services.review_service import ReviewService

router = APIRouter(prefix="/api/review", tags=["review"])
review_service = ReviewService()


class ReviewAnswerRequest(BaseModel):
    """复习答案提交请求"""
    user_id: str
    word_id: str
    user_answer: str


@router.get("/queue")
async def get_review_queue(user_id: str = Query(..., description="用户ID")):
    """获取复习队列
    
    根据需求 3.1：优先展示高频错词
    
    Args:
        user_id: 用户ID
        
    Returns:
        复习队列列表，按错误次数降序排列
    """
    try:
        queue = review_service.get_review_queue(user_id)
        return queue
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取复习队列失败: {str(e)}")


@router.get("/info/{word_id}")
async def get_review_info(
    word_id: str,
    user_id: str = Query(..., description="用户ID")
):
    """获取单词的复习信息
    
    根据需求 3.2：显示该单词的历史错误次数和上次复习时间
    
    Args:
        word_id: 单词ID
        user_id: 用户ID
        
    Returns:
        包含错误次数和上次复习时间的字典
    """
    try:
        info = review_service.get_review_info(user_id, word_id)
        return info
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取复习信息失败: {str(e)}")


@router.post("/submit")
async def submit_review_answer(request: ReviewAnswerRequest):
    """提交复习答案
    
    根据需求 3.3：更新该单词的复习状态和时间戳
    
    Args:
        request: 包含用户ID、单词ID和用户答案的请求
        
    Returns:
        答案验证结果和更新后的学习记录
    """
    try:
        # 获取单词信息以验证答案
        info = review_service.get_review_info(request.user_id, request.word_id)
        correct_answer = info['word']
        
        # 验证答案（忽略大小写和首尾空格）
        is_correct = request.user_answer.strip().lower() == correct_answer.strip().lower()
        
        # 更新复习状态
        learning_record = review_service.update_review_status(
            request.user_id,
            request.word_id,
            is_correct
        )
        
        return {
            'is_correct': is_correct,
            'correct_answer': correct_answer,
            'learning_record': {
                'status': learning_record.status,
                'last_review_time': learning_record.last_review_time,
                'next_review_time': learning_record.next_review_time,
                'review_count': learning_record.review_count
            }
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"提交复习答案失败: {str(e)}")


@router.get("/due")
async def get_words_due_for_review(user_id: str = Query(..., description="用户ID")):
    """获取到期需要复习的单词
    
    Args:
        user_id: 用户ID
        
    Returns:
        到期复习的单词列表
    """
    try:
        words = review_service.get_words_due_for_review(user_id)
        return words
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取到期复习单词失败: {str(e)}")
