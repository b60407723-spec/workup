"""MapReduce 服务 - 支持本地模式和 Hadoop 集群模式"""
import os
import sys
import time
import subprocess
import uuid
from typing import List, Dict, Optional
from pathlib import Path
from datetime import datetime
from ..models import MapReduceJob
from ..repositories.error_record_repository import ErrorRecordRepository
from ..repositories.word_repository import WordRepository
from ..repositories.mapreduce_job_repository import MapReduceJobRepository
from ..middleware.metrics import (
    record_mapreduce_job,
    record_hdfs_operation,
    increment_jobs_in_progress,
    decrement_jobs_in_progress,
)


class MapReduceService:
    """MapReduce 分析服务
    
    支持两种运行模式：
    1. local - 本地模拟模式（默认，用于开发测试）
    2. hadoop - Hadoop 集群模式（用于生产环境）
    """
    
    # Hadoop 配置（可通过环境变量覆盖）
    HADOOP_HOME = os.environ.get('HADOOP_HOME', '/usr/local/hadoop')
    HADOOP_STREAMING_JAR = os.environ.get(
        'HADOOP_STREAMING_JAR', 
        '/usr/local/hadoop/share/hadoop/tools/lib/hadoop-streaming-*.jar'
    )
    HDFS_INPUT_DIR = os.environ.get('HDFS_INPUT_DIR', '/user/wordmemory/input')
    HDFS_OUTPUT_DIR = os.environ.get('HDFS_OUTPUT_DIR', '/user/wordmemory/output')
    
    # 运行模式：local 或 hadoop
    RUN_MODE = os.environ.get('MAPREDUCE_MODE', 'local')
    
    def __init__(
        self,
        error_repo: Optional[ErrorRecordRepository] = None,
        word_repo: Optional[WordRepository] = None,
        mode: Optional[str] = None
    ):
        """初始化 MapReduceService
        
        Args:
            error_repo: 错词记录 Repository
            word_repo: 单词 Repository
            mode: 运行模式 ('local' 或 'hadoop')，默认从环境变量读取
        """
        self.error_repo = error_repo or ErrorRecordRepository()
        self.word_repo = word_repo or WordRepository()
        self.job_repo = MapReduceJobRepository()  # 持久化存储作业状态
        self.mode = mode or self.RUN_MODE
        
        # 获取项目根目录
        self.project_root = Path(__file__).parent.parent.parent
        self.mapreduce_dir = self.project_root / "mapreduce"
        self.data_dir = self.project_root / "data"
        
    def trigger_analysis(self, user_id: str = "default", use_hadoop: bool = False) -> str:
        """触发 MapReduce 分析
        
        Args:
            user_id: 用户 ID
            use_hadoop: 是否强制使用 Hadoop 模式
            
        Returns:
            作业 ID
        """
        job_id = str(uuid.uuid4())
        run_mode = 'hadoop' if use_hadoop else self.mode
        
        # 创建作业记录（持久化）
        self.job_repo.save(MapReduceJob(
            id=job_id,
            user_id=user_id,
            mode=run_mode,
            status='running',
            start_time=datetime.now(),
            end_time=None,
            input_count=0,
            error=None,
            result=None
        ))
        
        increment_jobs_in_progress()
        started_at = time.time()
        try:
            if run_mode == 'hadoop':
                success = self._run_hadoop_job(job_id, user_id)
            else:
                success = self._run_local_job(job_id, user_id)
            
            self._update_job(
                job_id,
                status='completed' if success else 'failed',
                end_time=datetime.now()
            )
                
        except Exception as e:
            self._update_job(job_id, status='failed', error=str(e), end_time=datetime.now())
        finally:
            decrement_jobs_in_progress()
            job = self.job_repo.find_by_id(job_id)
            record_mapreduce_job(
                mode=run_mode,
                status='success' if job and job.status == 'completed' else 'failed',
                duration=time.time() - started_at,
                records_count=job.input_count if job else 0
            )
        
        return job_id
    
    def _update_job(self, job_id: str, **fields) -> None:
        """更新作业字段并持久化
        
        Args:
            job_id: 作业 ID
            fields: 需要更新的字段（如 status、end_time、error、result、input_count）
        """
        job = self.job_repo.find_by_id(job_id)
        if job is None:
            return
        for key, value in fields.items():
            setattr(job, key, value)
        self.job_repo.update(job)
    
    @staticmethod
    def _job_to_status_dict(job: MapReduceJob) -> Dict:
        """将作业对象转换为状态字典（兼容路由响应模型）"""
        return {
            'status': job.status,
            'user_id': job.user_id,
            'mode': job.mode,
            'start_time': job.start_time.isoformat() if isinstance(job.start_time, datetime) else job.start_time,
            'end_time': job.end_time.isoformat() if job.end_time and isinstance(job.end_time, datetime) else job.end_time,
            'input_count': job.input_count,
            'error': job.error,
            'result': job.result
        }
    
    def _run_local_job(self, job_id: str, user_id: str) -> bool:
        """运行本地模式的 MapReduce 作业"""
        try:
            input_file = self.data_dir / f"mapreduce_input_{job_id}.txt"
            output_file = self.data_dir / f"mapreduce_output_{job_id}.txt"
            
            # 准备输入数据
            error_records = self.error_repo.find_by_user(user_id) if user_id != "default" else self.error_repo.find_all()
            self._update_job(job_id, input_count=len(error_records))
            
            with open(input_file, 'w', encoding='utf-8') as f:
                for record in error_records:
                    f.write(f"{record.word_id}\t{record.user_id}\t{record.wrong_answer}\t{record.timestamp.isoformat()}\n")
            
            # 运行本地 MapReduce
            success = self.run_local_test(str(input_file), str(output_file))
            
            if success:
                results = self._parse_results(str(output_file), user_id)
                self._update_job(job_id, result=results)
            
            # 清理输入文件
            if input_file.exists():
                input_file.unlink()
                
            return success
            
        except Exception as e:
            self._update_job(job_id, error=str(e))
            return False
    
    def _run_hadoop_job(self, job_id: str, user_id: str) -> bool:
        """运行 Hadoop 集群模式的 MapReduce 作业
        
        这个方法会：
        1. 将数据上传到 HDFS
        2. 提交 Hadoop Streaming 作业
        3. 等待作业完成
        4. 从 HDFS 下载结果
        """
        try:
            # 检查 Hadoop 是否可用
            if not self._check_hadoop_available():
                self._update_job(job_id, error='Hadoop 不可用，请检查 HADOOP_HOME 配置')
                return False
            
            # 准备本地输入文件
            local_input = self.data_dir / f"mapreduce_input_{job_id}.txt"
            local_output = self.data_dir / f"mapreduce_output_{job_id}.txt"
            
            # HDFS 路径
            hdfs_input = f"{self.HDFS_INPUT_DIR}/{job_id}"
            hdfs_output = f"{self.HDFS_OUTPUT_DIR}/{job_id}"
            
            # 1. 准备输入数据
            error_records = self.error_repo.find_by_user(user_id) if user_id != "default" else self.error_repo.find_all()
            self._update_job(job_id, input_count=len(error_records))
            
            with open(local_input, 'w', encoding='utf-8') as f:
                for record in error_records:
                    f.write(f"{record.word_id}\t{record.user_id}\t{record.wrong_answer}\t{record.timestamp.isoformat()}\n")
            
            # 2. 创建 HDFS 目录并上传输入文件
            self._hdfs_mkdir(hdfs_input)
            self._hdfs_put(str(local_input), f"{hdfs_input}/input.txt")
            
            # 3. 删除可能存在的输出目录
            self._hdfs_rm(hdfs_output)
            
            # 4. 提交 Hadoop Streaming 作业
            mapper_path = self.mapreduce_dir / "mapper.py"
            reducer_path = self.mapreduce_dir / "reducer.py"
            
            hadoop_cmd = [
                f"{self.HADOOP_HOME}/bin/hadoop", "jar",
                self._find_streaming_jar(),
                "-files", f"{mapper_path},{reducer_path}",
                "-mapper", "python3 mapper.py",
                "-reducer", "python3 reducer.py",
                "-input", f"{hdfs_input}/input.txt",
                "-output", hdfs_output
            ]
            
            print(f"执行 Hadoop 命令: {' '.join(hadoop_cmd)}")
            
            result = subprocess.run(
                hadoop_cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5分钟超时
            )
            
            if result.returncode != 0:
                self._update_job(job_id, error=f"Hadoop 作业失败: {result.stderr}")
                return False
            
            # 5. 下载结果
            self._hdfs_get(f"{hdfs_output}/part-00000", str(local_output))
            
            # 6. 解析结果
            results = self._parse_results(str(local_output), user_id)
            self._update_job(job_id, result=results)
            
            # 7. 清理
            if local_input.exists():
                local_input.unlink()
            self._hdfs_rm(hdfs_input)
            self._hdfs_rm(hdfs_output)
            
            return True
            
        except subprocess.TimeoutExpired:
            self._update_job(job_id, error='Hadoop 作业超时')
            return False
        except Exception as e:
            self._update_job(job_id, error=str(e))
            return False
    
    def _check_hadoop_available(self) -> bool:
        """检查 Hadoop 是否可用"""
        try:
            hadoop_bin = Path(self.HADOOP_HOME) / "bin" / "hadoop"
            if sys.platform == 'win32':
                hadoop_bin = Path(self.HADOOP_HOME) / "bin" / "hadoop.cmd"
            
            result = subprocess.run(
                [str(hadoop_bin), "version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0
        except Exception:
            return False
    
    def _find_streaming_jar(self) -> str:
        """查找 Hadoop Streaming JAR 文件"""
        import glob
        
        # 尝试从环境变量获取
        if os.path.exists(self.HADOOP_STREAMING_JAR):
            return self.HADOOP_STREAMING_JAR
        
        # 搜索常见位置
        patterns = [
            f"{self.HADOOP_HOME}/share/hadoop/tools/lib/hadoop-streaming-*.jar",
            f"{self.HADOOP_HOME}/contrib/streaming/hadoop-streaming-*.jar",
        ]
        
        for pattern in patterns:
            matches = glob.glob(pattern)
            if matches:
                return matches[0]
        
        raise FileNotFoundError("找不到 Hadoop Streaming JAR 文件")
    
    def _hdfs_mkdir(self, path: str):
        """在 HDFS 创建目录"""
        subprocess.run(
            [f"{self.HADOOP_HOME}/bin/hdfs", "dfs", "-mkdir", "-p", path],
            capture_output=True
        )
        record_hdfs_operation('mkdir')
    
    def _hdfs_put(self, local_path: str, hdfs_path: str):
        """上传文件到 HDFS"""
        result = subprocess.run(
            [f"{self.HADOOP_HOME}/bin/hdfs", "dfs", "-put", "-f", local_path, hdfs_path],
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            raise Exception(f"HDFS 上传失败: {result.stderr}")
        try:
            record_hdfs_operation('put', os.path.getsize(local_path))
        except OSError:
            record_hdfs_operation('put')
    
    def _hdfs_get(self, hdfs_path: str, local_path: str):
        """从 HDFS 下载文件"""
        result = subprocess.run(
            [f"{self.HADOOP_HOME}/bin/hdfs", "dfs", "-get", "-f", hdfs_path, local_path],
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            raise Exception(f"HDFS 下载失败: {result.stderr}")
        try:
            record_hdfs_operation('get', os.path.getsize(local_path))
        except OSError:
            record_hdfs_operation('get')
    
    def _hdfs_rm(self, path: str):
        """删除 HDFS 文件/目录"""
        subprocess.run(
            [f"{self.HADOOP_HOME}/bin/hdfs", "dfs", "-rm", "-r", "-f", path],
            capture_output=True
        )
        record_hdfs_operation('delete')
    
    def get_job_status(self, job_id: str) -> Dict:
        """获取作业状态"""
        job = self.job_repo.find_by_id(job_id)
        if job is None:
            return {
                'status': 'not_found',
                'error': f'Job {job_id} not found'
            }
        return self._job_to_status_dict(job)
    
    def get_analysis_results(self, user_id: str = "default", job_id: Optional[str] = None) -> List[Dict]:
        """获取分析结果（高频错词）"""
        if job_id:
            job = self.job_repo.find_by_id(job_id)
            if job is None:
                return []
            if job.status != 'completed' or not job.result:
                return []
            return job.result
        else:
            new_job_id = self.trigger_analysis(user_id)
            job = self.job_repo.find_by_id(new_job_id)
            if job and job.status == 'completed' and job.result:
                return job.result
            return []
    
    def run_local_test(self, input_file: str, output_file: str) -> bool:
        """运行本地测试模式（模拟 MapReduce）"""
        mapper_path = self.mapreduce_dir / "mapper.py"
        reducer_path = self.mapreduce_dir / "reducer.py"
        
        try:
            # 步骤 1: 运行 Mapper
            with open(input_file, 'r', encoding='utf-8') as f:
                mapper_process = subprocess.Popen(
                    [sys.executable, str(mapper_path)],
                    stdin=f,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                mapper_output, mapper_errors = mapper_process.communicate()
            
            if not mapper_output.strip():
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write("")
                return True
            
            # 步骤 2: 排序 Mapper 输出
            sorted_output = '\n'.join(sorted(mapper_output.strip().split('\n')))
            
            # 步骤 3: 运行 Reducer
            reducer_process = subprocess.Popen(
                [sys.executable, str(reducer_path)],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            reducer_output, reducer_errors = reducer_process.communicate(input=sorted_output)
            
            # 步骤 4: 写入输出文件
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(reducer_output)
            
            return True
            
        except Exception as e:
            print(f"Error running MapReduce: {str(e)}", file=sys.stderr)
            return False
    
    def _parse_results(self, output_file: str, user_id: str) -> List[Dict]:
        """解析 MapReduce 结果"""
        results = []
        
        try:
            with open(output_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    
                    parts = line.split('\t')
                    if len(parts) >= 2:
                        word_id = parts[0]
                        error_count = int(parts[1])
                        
                        word = self.word_repo.find_by_id(word_id)
                        
                        if word:
                            results.append({
                                'word_id': word_id,
                                'word': word.word,
                                'definition': word.definition,
                                'part_of_speech': word.part_of_speech,
                                'error_count': error_count
                            })
                        else:
                            results.append({
                                'word_id': word_id,
                                'word': 'Unknown',
                                'definition': 'Unknown',
                                'part_of_speech': 'Unknown',
                                'error_count': error_count
                            })
        except Exception as e:
            print(f"Error parsing results: {str(e)}", file=sys.stderr)
        
        return results
    
    def get_mode_info(self) -> Dict:
        """获取当前运行模式信息"""
        hadoop_available = self._check_hadoop_available()
        
        return {
            'current_mode': self.mode,
            'hadoop_available': hadoop_available,
            'hadoop_home': self.HADOOP_HOME,
            'hdfs_input_dir': self.HDFS_INPUT_DIR,
            'hdfs_output_dir': self.HDFS_OUTPUT_DIR,
            'instructions': {
                'local': '本地模式：使用 Python 模拟 MapReduce 流程',
                'hadoop': 'Hadoop 模式：提交作业到 Hadoop 集群执行'
            },
            'env_vars': {
                'MAPREDUCE_MODE': '设置运行模式 (local/hadoop)',
                'HADOOP_HOME': 'Hadoop 安装目录',
                'HADOOP_STREAMING_JAR': 'Hadoop Streaming JAR 路径',
                'HDFS_INPUT_DIR': 'HDFS 输入目录',
                'HDFS_OUTPUT_DIR': 'HDFS 输出目录'
            }
        }
