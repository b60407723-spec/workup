"""统计分析 API 路由"""
from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict

from ..services.statistics_service import StatisticsService


router = APIRouter(prefix="/api/stats", tags=["statistics"])
stats_service = StatisticsService()


class OverallStatsResponse(BaseModel):
    """总体统计响应模型"""
    total_words: int
    mastered_count: int
    learning_count: int
    reviewing_count: int
    unlearned_count: int
    test_count: int
    average_accuracy: float


class DifficultyDistributionResponse(BaseModel):
    """难度分布响应模型"""
    difficulty_1: Dict
    difficulty_2: Dict
    difficulty_3: Dict
    difficulty_4: Dict
    difficulty_5: Dict


class POSAnalysisResponse(BaseModel):
    """词性分析响应模型"""
    data: Dict[str, Dict]


class TimeTrendResponse(BaseModel):
    """时间趋势响应模型"""
    dates: List[str]
    learned_words: List[int]
    test_count: List[int]
    error_count: List[int]


@router.get("/overall", response_model=OverallStatsResponse)
async def get_overall_stats(
    user_id: str = Query("default_user", description="用户ID")
):
    """获取总体统计数据
    
    Args:
        user_id: 用户ID（默认为 default_user）
        
    Returns:
        总体统计数据，包括总学习单词数、已掌握数量、测试次数、平均正确率等
    """
    try:
        stats = stats_service.get_overall_stats(user_id)
        return OverallStatsResponse(**stats)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "code": "STATS_ERROR",
                "message": f"获取统计数据失败: {str(e)}",
                "details": []
            }
        )


@router.get("/difficulty", response_model=DifficultyDistributionResponse)
async def get_difficulty_distribution(
    user_id: str = Query("default_user", description="用户ID")
):
    """获取难度分布统计
    
    Args:
        user_id: 用户ID（默认为 default_user）
        
    Returns:
        各难度等级的单词分布和学习情况
    """
    try:
        distribution = stats_service.get_difficulty_distribution(user_id)
        return DifficultyDistributionResponse(**distribution)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "code": "STATS_ERROR",
                "message": f"获取难度分布失败: {str(e)}",
                "details": []
            }
        )


@router.get("/pos", response_model=POSAnalysisResponse)
async def get_pos_analysis(
    user_id: str = Query("default_user", description="用户ID")
):
    """获取词性分析统计
    
    Args:
        user_id: 用户ID（默认为 default_user）
        
    Returns:
        各词性的单词分布和错误情况
    """
    try:
        analysis = stats_service.get_pos_analysis(user_id)
        return POSAnalysisResponse(data=analysis)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "code": "STATS_ERROR",
                "message": f"获取词性分析失败: {str(e)}",
                "details": []
            }
        )


@router.get("/trend", response_model=TimeTrendResponse)
async def get_time_trend(
    user_id: str = Query("default_user", description="用户ID"),
    start_date: Optional[str] = Query(None, description="开始日期 (ISO格式)"),
    end_date: Optional[str] = Query(None, description="结束日期 (ISO格式)"),
    granularity: str = Query("day", description="时间粒度 (day 或 week)")
):
    """获取时间趋势统计
    
    Args:
        user_id: 用户ID（默认为 default_user）
        start_date: 开始日期（可选，默认为30天前）
        end_date: 结束日期（可选，默认为今天）
        granularity: 时间粒度（day 或 week，默认为 day）
        
    Returns:
        时间序列数据，包括每日/每周的学习单词数、测试次数、错误次数
    """
    try:
        # 验证时间粒度
        if granularity not in ['day', 'week']:
            raise HTTPException(
                status_code=400,
                detail={
                    "code": "INVALID_GRANULARITY",
                    "message": "时间粒度必须是 'day' 或 'week'",
                    "details": []
                }
            )
        
        trend = stats_service.get_time_trend(user_id, start_date, end_date, granularity)
        return TimeTrendResponse(**trend)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "code": "STATS_ERROR",
                "message": f"获取时间趋势失败: {str(e)}",
                "details": []
            }
        )
