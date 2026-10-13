"""服务层模块"""
from .word_service import WordService
from .test_service import TestService
from .review_service import ReviewService
from .statistics_service import StatisticsService
from .mapreduce_service import MapReduceService
from .dictation_service import DictationService

__all__ = ['WordService', 'TestService', 'ReviewService', 'StatisticsService', 'MapReduceService', 'DictationService']
