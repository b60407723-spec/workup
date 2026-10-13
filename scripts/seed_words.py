"""填充常用英语单词数据"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.services.word_service import WordService

# 常用英语单词列表（包含单词、释义、词性、难度）
COMMON_WORDS = [
    # 难度1 - 基础词汇
    ("apple", "苹果", "noun", 1),
    ("book", "书", "noun", 1),
    ("cat", "猫", "noun", 1),
    ("dog", "狗", "noun", 1),
    ("eat", "吃", "verb", 1),
    ("fish", "鱼", "noun", 1),
    ("good", "好的", "adj", 1),
    ("happy", "快乐的", "adj", 1),
    ("ice", "冰", "noun", 1),
    ("jump", "跳", "verb", 1),
    ("king", "国王", "noun", 1),
    ("love", "爱", "verb", 1),
    ("milk", "牛奶", "noun", 1),
    ("name", "名字", "noun", 1),
    ("open", "打开", "verb", 1),
    ("play", "玩", "verb", 1),
    ("queen", "女王", "noun", 1),
    ("run", "跑", "verb", 1),
    ("sun", "太阳", "noun", 1),
    ("tree", "树", "noun", 1),
    ("under", "在...下面", "prep", 1),
    ("very", "非常", "adv", 1),
    ("water", "水", "noun", 1),
    ("year", "年", "noun", 1),
    ("zero", "零", "noun", 1),
    
    # 难度2 - 初级词汇
    ("beautiful", "美丽的", "adj", 2),
    ("breakfast", "早餐", "noun", 2),
    ("children", "孩子们", "noun", 2),
    ("different", "不同的", "adj", 2),
    ("example", "例子", "noun", 2),
    ("family", "家庭", "noun", 2),
    ("garden", "花园", "noun", 2),
    ("hospital", "医院", "noun", 2),
    ("important", "重要的", "adj", 2),
    ("journey", "旅程", "noun", 2),
    ("kitchen", "厨房", "noun", 2),
    ("library", "图书馆", "noun", 2),
    ("mountain", "山", "noun", 2),
    ("natural", "自然的", "adj", 2),
    ("orange", "橙子", "noun", 2),
    ("problem", "问题", "noun", 2),
    ("question", "问题", "noun", 2),
    ("remember", "记住", "verb", 2),
    ("student", "学生", "noun", 2),
    ("teacher", "老师", "noun", 2),
    ("understand", "理解", "verb", 2),
    ("village", "村庄", "noun", 2),
    ("weather", "天气", "noun", 2),
    ("yesterday", "昨天", "noun", 2),
    ("together", "一起", "adv", 2),
    
    # 难度3 - 中级词汇
    ("adventure", "冒险", "noun", 3),
    ("behavior", "行为", "noun", 3),
    ("celebrate", "庆祝", "verb", 3),
    ("decision", "决定", "noun", 3),
    ("education", "教育", "noun", 3),
    ("fortunate", "幸运的", "adj", 3),
    ("government", "政府", "noun", 3),
    ("happiness", "幸福", "noun", 3),
    ("imagination", "想象力", "noun", 3),
    ("knowledge", "知识", "noun", 3),
    ("literature", "文学", "noun", 3),
    ("mysterious", "神秘的", "adj", 3),
    ("necessary", "必要的", "adj", 3),
    ("opportunity", "机会", "noun", 3),
    ("particular", "特别的", "adj", 3),
    ("recognize", "认出", "verb", 3),
    ("situation", "情况", "noun", 3),
    ("technology", "技术", "noun", 3),
    ("university", "大学", "noun", 3),
    ("vocabulary", "词汇", "noun", 3),
    ("wonderful", "精彩的", "adj", 3),
    ("experience", "经验", "noun", 3),
    ("environment", "环境", "noun", 3),
    ("communicate", "交流", "verb", 3),
    ("appreciate", "欣赏", "verb", 3),
    
    # 难度4 - 中高级词汇
    ("accomplish", "完成", "verb", 4),
    ("beneficial", "有益的", "adj", 4),
    ("consequence", "后果", "noun", 4),
    ("demonstrate", "展示", "verb", 4),
    ("enthusiasm", "热情", "noun", 4),
    ("fundamental", "基本的", "adj", 4),
    ("guarantee", "保证", "verb", 4),
    ("hypothesis", "假设", "noun", 4),
    ("independent", "独立的", "adj", 4),
    ("justification", "理由", "noun", 4),
    ("magnificent", "壮丽的", "adj", 4),
    ("nevertheless", "然而", "adv", 4),
    ("observation", "观察", "noun", 4),
    ("perspective", "观点", "noun", 4),
    ("qualification", "资格", "noun", 4),
    ("responsibility", "责任", "noun", 4),
    ("significant", "重要的", "adj", 4),
    ("transformation", "转变", "noun", 4),
    ("unfortunately", "不幸地", "adv", 4),
    ("vulnerability", "脆弱性", "noun", 4),
    ("acknowledge", "承认", "verb", 4),
    ("comprehensive", "全面的", "adj", 4),
    ("determination", "决心", "noun", 4),
    ("extraordinary", "非凡的", "adj", 4),
    ("implementation", "实施", "noun", 4),
    
    # 难度5 - 高级词汇
    ("accommodate", "容纳", "verb", 5),
    ("bureaucracy", "官僚主义", "noun", 5),
    ("conscientious", "认真的", "adj", 5),
    ("deteriorate", "恶化", "verb", 5),
    ("exaggerate", "夸张", "verb", 5),
    ("fluctuate", "波动", "verb", 5),
    ("gregarious", "群居的", "adj", 5),
    ("hierarchical", "等级制的", "adj", 5),
    ("idiosyncratic", "独特的", "adj", 5),
    ("juxtaposition", "并列", "noun", 5),
    ("kaleidoscope", "万花筒", "noun", 5),
    ("loquacious", "健谈的", "adj", 5),
    ("meticulous", "一丝不苟的", "adj", 5),
    ("nonchalant", "漠不关心的", "adj", 5),
    ("ostentatious", "炫耀的", "adj", 5),
    ("paradigm", "范例", "noun", 5),
    ("quintessential", "典型的", "adj", 5),
    ("reciprocate", "回报", "verb", 5),
    ("serendipity", "意外发现", "noun", 5),
    ("ubiquitous", "无处不在的", "adj", 5),
    ("vicarious", "间接的", "adj", 5),
    ("whimsical", "异想天开的", "adj", 5),
    ("xenophobia", "仇外心理", "noun", 5),
    ("zealous", "热心的", "adj", 5),
    ("ambiguous", "模糊的", "adj", 5),
]


def seed_words():
    """填充单词数据"""
    word_service = WordService()
    
    success_count = 0
    skip_count = 0
    fail_count = 0
    
    print("开始填充单词数据...")
    print(f"共 {len(COMMON_WORDS)} 个单词待添加\n")
    
    for word, definition, pos, difficulty in COMMON_WORDS:
        word_data = {
            "word": word,
            "definition": definition,
            "part_of_speech": pos,
            "difficulty": difficulty
        }
        
        result, error = word_service.add_word(word_data)
        
        if result:
            success_count += 1
            print(f"✓ 添加: {word} ({pos}, 难度{difficulty})")
        elif "已存在" in str(error):
            skip_count += 1
            print(f"- 跳过: {word} (已存在)")
        else:
            fail_count += 1
            print(f"✗ 失败: {word} - {error}")
    
    print(f"\n完成！")
    print(f"  成功添加: {success_count}")
    print(f"  已存在跳过: {skip_count}")
    print(f"  添加失败: {fail_count}")
    print(f"  总计: {success_count + skip_count + fail_count}")


if __name__ == "__main__":
    seed_words()
