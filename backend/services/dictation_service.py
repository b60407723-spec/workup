"""默写本生成服务"""
from typing import List, Dict, Optional
from datetime import datetime
from io import BytesIO

from ..services.mapreduce_service import MapReduceService


class DictationService:
    """默写本生成业务逻辑"""
    
    def __init__(self, mapreduce_service: Optional[MapReduceService] = None):
        """初始化 DictationService
        
        Args:
            mapreduce_service: MapReduce 服务实例
        """
        self.mapreduce_service = mapreduce_service or MapReduceService()
    
    def generate_dictation_book(
        self, 
        user_id: str = "default", 
        top_n: int = 50, 
        format: str = "txt"
    ) -> bytes:
        """生成默写本文件
        
        Args:
            user_id: 用户 ID
            top_n: 包含的单词数量（前 N 个高频错词）
            format: 文件格式（txt 或 pdf）
            
        Returns:
            文件内容（字节）
        """
        # 获取高频错词数据
        high_frequency_words = self._get_high_frequency_words(user_id, top_n)
        
        # 根据格式生成文件
        if format.lower() == "pdf":
            return self.format_as_pdf(high_frequency_words)
        else:
            # 默认使用 TXT 格式
            return self.format_as_txt(high_frequency_words).encode('utf-8')
    
    def _get_high_frequency_words(self, user_id: str, top_n: int) -> List[Dict]:
        """基于 MapReduce 结果选择高频错词
        
        Args:
            user_id: 用户 ID
            top_n: 返回前 N 个单词
            
        Returns:
            高频错词列表（已按错误次数降序排列）
        """
        # 获取 MapReduce 分析结果
        results = self.mapreduce_service.get_analysis_results(user_id)
        
        # 结果已经按错误次数降序排列，直接取前 N 个
        return results[:top_n]
    
    def format_as_txt(self, words: List[Dict]) -> str:
        """格式化为 TXT
        
        Args:
            words: 高频错词列表
            
        Returns:
            TXT 格式的字符串
        """
        if not words:
            return "暂无错词记录\n"
        
        lines = []
        lines.append("=" * 60)
        lines.append("英语单词默写本")
        lines.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"单词数量: {len(words)}")
        lines.append("=" * 60)
        lines.append("")
        
        for idx, word_data in enumerate(words, start=1):
            lines.append(f"{idx}. {word_data['word']}")
            lines.append(f"   中文释义: {word_data['definition']}")
            lines.append(f"   词性: {word_data['part_of_speech']}")
            lines.append(f"   错误次数: {word_data['error_count']}")
            lines.append("")
        
        lines.append("=" * 60)
        lines.append("提示：请根据中文释义默写英文单词")
        lines.append("=" * 60)
        
        return "\n".join(lines)
    
    def format_as_pdf(self, words: List[Dict]) -> bytes:
        """格式化为 PDF（可选功能）
        
        Args:
            words: 高频错词列表
            
        Returns:
            PDF 格式的字节数据
        """
        try:
            from reportlab.lib.pagesizes import letter, A4
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import inch
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
            from reportlab.lib import colors
            from reportlab.pdfbase import pdfmetrics
            from reportlab.pdfbase.ttfonts import TTFont
            
            # 创建 PDF 缓冲区
            buffer = BytesIO()
            
            # 创建 PDF 文档
            doc = SimpleDocTemplate(buffer, pagesize=A4)
            story = []
            
            # 尝试注册中文字体（如果可用）
            try:
                # 这里需要系统中有中文字体文件
                # 在实际部署时需要配置字体路径
                pdfmetrics.registerFont(TTFont('SimSun', 'simsun.ttc'))
                chinese_font = 'SimSun'
            except:
                # 如果没有中文字体，使用默认字体（可能无法显示中文）
                chinese_font = 'Helvetica'
            
            # 定义样式
            styles = getSampleStyleSheet()
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontName=chinese_font,
                fontSize=24,
                textColor=colors.HexColor('#333333'),
                spaceAfter=30,
                alignment=1  # 居中
            )
            
            normal_style = ParagraphStyle(
                'CustomNormal',
                parent=styles['Normal'],
                fontName=chinese_font,
                fontSize=12,
                textColor=colors.HexColor('#333333')
            )
            
            # 添加标题
            story.append(Paragraph("英语单词默写本", title_style))
            story.append(Spacer(1, 0.2 * inch))
            
            # 添加生成信息
            info_text = f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}<br/>单词数量: {len(words)}"
            story.append(Paragraph(info_text, normal_style))
            story.append(Spacer(1, 0.3 * inch))
            
            # 创建单词表格
            if words:
                table_data = [['序号', '单词', '中文释义', '词性', '错误次数']]
                
                for idx, word_data in enumerate(words, start=1):
                    table_data.append([
                        str(idx),
                        word_data['word'],
                        word_data['definition'],
                        word_data['part_of_speech'],
                        str(word_data['error_count'])
                    ])
                
                # 创建表格
                table = Table(table_data, colWidths=[0.8*inch, 1.5*inch, 2.5*inch, 1*inch, 1*inch])
                
                # 设置表格样式
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), chinese_font),
                    ('FONTSIZE', (0, 0), (-1, 0), 12),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('FONTNAME', (0, 1), (-1, -1), chinese_font),
                    ('FONTSIZE', (0, 1), (-1, -1), 10),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                
                story.append(table)
            else:
                story.append(Paragraph("暂无错词记录", normal_style))
            
            story.append(Spacer(1, 0.3 * inch))
            story.append(Paragraph("提示：请根据中文释义默写英文单词", normal_style))
            
            # 生成 PDF
            doc.build(story)
            
            # 获取 PDF 内容
            pdf_content = buffer.getvalue()
            buffer.close()
            
            return pdf_content
            
        except ImportError:
            # 如果 reportlab 未安装，返回错误信息
            error_msg = "PDF 生成功能需要安装 reportlab 库\n请运行: pip install reportlab"
            return error_msg.encode('utf-8')
        except Exception as e:
            # 其他错误
            error_msg = f"生成 PDF 时发生错误: {str(e)}"
            return error_msg.encode('utf-8')
