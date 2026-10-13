"""MapReduce 分析 API 路由"""
from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional

from ..services.mapreduce_service import MapReduceService


router = APIRouter(prefix="/api/mapreduce", tags=["mapreduce"])
mapreduce_service = MapReduceService()


class TriggerAnalysisResponse(BaseModel):
    """触发分析响应模型"""
    job_id: str
    message: str
    mode: str


class JobStatusResponse(BaseModel):
    """作业状态响应模型"""
    status: str
    user_id: Optional[str] = None
    mode: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    error: Optional[str] = None


class HighFrequencyWord(BaseModel):
    """高频错词模型"""
    word_id: str
    word: str
    definition: str
    part_of_speech: str
    error_count: int


class AnalysisResultsResponse(BaseModel):
    """分析结果响应模型"""
    results: List[HighFrequencyWord]
    total_count: int


class ModeInfoResponse(BaseModel):
    """模式信息响应模型"""
    current_mode: str
    hadoop_available: bool
    hadoop_home: str
    hdfs_input_dir: str
    hdfs_output_dir: str
    instructions: Dict[str, str]
    env_vars: Dict[str, str]


@router.post("/trigger", response_model=TriggerAnalysisResponse)
async def trigger_analysis(
    user_id: str = Query("default", description="用户ID"),
    use_hadoop: bool = Query(False, description="是否强制使用 Hadoop 模式")
):
    """触发 MapReduce 分析
    
    Args:
        user_id: 用户ID（默认为 default，分析所有用户数据）
        use_hadoop: 是否强制使用 Hadoop 模式（默认使用环境变量配置的模式）
        
    Returns:
        作业ID和提示信息
    """
    try:
        job_id = mapreduce_service.trigger_analysis(user_id, use_hadoop)
        job_status = mapreduce_service.get_job_status(job_id)
        
        return TriggerAnalysisResponse(
            job_id=job_id,
            message=f"MapReduce 分析已启动，作业ID: {job_id}",
            mode=job_status.get('mode', 'local')
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "code": "MAPREDUCE_ERROR",
                "message": f"触发 MapReduce 分析失败: {str(e)}",
                "details": []
            }
        )


@router.get("/status/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: str):
    """查询作业状态
    
    Args:
        job_id: 作业ID
        
    Returns:
        作业状态信息
    """
    try:
        status = mapreduce_service.get_job_status(job_id)
        
        if status.get('status') == 'not_found':
            raise HTTPException(
                status_code=404,
                detail={
                    "code": "JOB_NOT_FOUND",
                    "message": f"作业 {job_id} 不存在",
                    "details": []
                }
            )
        
        return JobStatusResponse(
            status=status['status'],
            user_id=status.get('user_id'),
            mode=status.get('mode'),
            start_time=status.get('start_time'),
            end_time=status.get('end_time'),
            error=status.get('error')
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "code": "MAPREDUCE_ERROR",
                "message": f"查询作业状态失败: {str(e)}",
                "details": []
            }
        )


@router.get("/results", response_model=AnalysisResultsResponse)
async def get_analysis_results(
    user_id: str = Query("default", description="用户ID"),
    job_id: Optional[str] = Query(None, description="作业ID（可选）"),
    top_n: int = Query(50, description="返回前N个高频错词", ge=1, le=1000)
):
    """获取分析结果（高频错词）
    
    Args:
        user_id: 用户ID（默认为 default）
        job_id: 作业ID（可选，如果不提供则运行新的分析）
        top_n: 返回前N个高频错词（默认50，最大1000）
        
    Returns:
        高频错词列表
    """
    try:
        results = mapreduce_service.get_analysis_results(user_id, job_id)
        
        # 限制返回数量
        limited_results = results[:top_n]
        
        # 转换为响应模型
        high_frequency_words = [
            HighFrequencyWord(**result) for result in limited_results
        ]
        
        return AnalysisResultsResponse(
            results=high_frequency_words,
            total_count=len(results)
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "code": "MAPREDUCE_ERROR",
                "message": f"获取分析结果失败: {str(e)}",
                "details": []
            }
        )


@router.get("/mode", response_model=ModeInfoResponse)
async def get_mode_info():
    """获取当前 MapReduce 运行模式信息
    
    Returns:
        当前模式、Hadoop 可用性、配置信息等
    """
    try:
        info = mapreduce_service.get_mode_info()
        return ModeInfoResponse(**info)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "code": "MAPREDUCE_ERROR",
                "message": f"获取模式信息失败: {str(e)}",
                "details": []
            }
        )
