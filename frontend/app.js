// 主应用逻辑
const API_BASE_URL = 'http://localhost:8000';

// 用户身份管理（避免 user_id 硬编码）
const USER_ID_STORAGE_KEY = 'wordup_user_id';
const DEFAULT_USER_ID = 'default_user';

function getUserId() {
    return localStorage.getItem(USER_ID_STORAGE_KEY) || DEFAULT_USER_ID;
}

function setUserId(userId) {
    const trimmed = (userId || '').trim();
    if (!trimmed) return;
    localStorage.setItem(USER_ID_STORAGE_KEY, trimmed);
}

// 头部用户切换控件初始化
function initUserSwitcher() {
    const input = document.getElementById('user-id-input');
    const button = document.getElementById('btn-user-apply');
    if (!input || !button) return;

    input.value = getUserId();

    button.addEventListener('click', () => {
        const value = input.value.trim();
        if (!value) {
            input.value = getUserId();
            return;
        }
        if (value === getUserId()) return;
        setUserId(value);
        // 重新加载页面，让各模块以新用户身份重新拉取数据
        window.location.reload();
    });

    input.addEventListener('keydown', (event) => {
        if (event.key === 'Enter') {
            button.click();
        }
    });
}

// 导航处理
document.getElementById('nav-learn').addEventListener('click', () => {
    loadModule('learn');
});

document.getElementById('nav-test').addEventListener('click', () => {
    loadModule('test');
});

document.getElementById('nav-review').addEventListener('click', () => {
    loadModule('review');
});

document.getElementById('nav-stats').addEventListener('click', () => {
    loadModule('stats');
});

document.getElementById('nav-manage').addEventListener('click', () => {
    loadModule('manage');
});

function loadModule(moduleName) {
    const mainContent = document.getElementById('main-content');
    
    switch(moduleName) {
        case 'learn':
            loadLearningModule(mainContent);
            break;
        case 'test':
            loadTestModule(mainContent);
            break;
        case 'review':
            loadReviewModule(mainContent);
            break;
        case 'stats':
            loadStatisticsModule(mainContent);
            break;
        case 'manage':
            loadManagementModule(mainContent);
            break;
        default:
            mainContent.innerHTML = `<h2>加载 ${moduleName} 模块...</h2>`;
    }
}

// 测试模块
class TestModule {
    constructor(container) {
        this.container = container;
        this.sessionId = null;
        this.words = [];
        this.currentWordIndex = 0;
        this.answers = new Map(); // word_id -> {userAnswer, isCorrect}
        this.init();
    }
    
    async init() {
        this.renderStartScreen();
    }
    
    renderStartScreen() {
        this.container.innerHTML = `
            <div class="test-module">
                <h2>单词测试</h2>
                
                <div class="test-start-screen">
                    <div class="test-intro">
                        <p>测试将随机选择单词，显示中文释义，请输入对应的英文单词。</p>
                        <p>完成测试后，系统会显示您的成绩和错词记录。</p>
                    </div>
                    
                    <div class="test-config">
                        <label for="word-count">测试单词数量：</label>
                        <input type="number" id="word-count" min="1" max="100" value="10">
                    </div>
                    
                    <button class="btn-start-test" id="btn-start-test">开始测试</button>
                </div>
            </div>
        `;
        
        document.getElementById('btn-start-test').addEventListener('click', () => {
            this.startTest();
        });
    }
    
    renderTestScreen() {
        const word = this.words[this.currentWordIndex];
        const progress = this.currentWordIndex + 1;
        const total = this.words.length;
        
        this.container.innerHTML = `
            <div class="test-module">
                <h2>单词测试</h2>
                
                <div class="test-progress">
                    <span>进度: ${progress} / ${total}</span>
                </div>
                
                <div class="test-question-area">
                    <div class="question-card">
                        <div class="question-label">请输入对应的英文单词：</div>
                        <div class="question-definition">${word.definition}</div>
                        <div class="question-meta">
                            <span class="word-pos ${this.getPosClass(word.part_of_speech)}">
                                ${this.getPosLabel(word.part_of_speech)}
                            </span>
                            <span class="word-difficulty">难度: ${'★'.repeat(word.difficulty)}</span>
                        </div>
                    </div>
                    
                    <div class="answer-input-area">
                        <input 
                            type="text" 
                            id="answer-input" 
                            class="answer-input" 
                            placeholder="输入英文单词..."
                            autocomplete="off"
                        >
                        <button class="btn-submit-answer" id="btn-submit-answer">提交答案</button>
                    </div>
                    
                    <div class="feedback-area" id="feedback-area"></div>
                </div>
            </div>
        `;
        
        const answerInput = document.getElementById('answer-input');
        const submitBtn = document.getElementById('btn-submit-answer');
        
        // 自动聚焦输入框
        answerInput.focus();
        
        // 回车提交
        answerInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.submitAnswer();
            }
        });
        
        submitBtn.addEventListener('click', () => {
            this.submitAnswer();
        });
    }
    
    renderResultScreen() {
        const correctCount = Array.from(this.answers.values()).filter(a => a.isCorrect).length;
        const wrongCount = this.answers.size - correctCount;
        const accuracy = this.answers.size > 0 ? (correctCount / this.answers.size * 100).toFixed(1) : 0;
        
        // 获取错词列表
        const wrongWords = [];
        this.answers.forEach((answer, wordId) => {
            if (!answer.isCorrect) {
                const word = this.words.find(w => w.word_id === wordId);
                if (word) {
                    wrongWords.push({
                        ...word,
                        userAnswer: answer.userAnswer,
                        correctAnswer: answer.correctAnswer
                    });
                }
            }
        });
        
        this.container.innerHTML = `
            <div class="test-module">
                <h2>测试结果</h2>
                
                <div class="test-result-screen">
                    <div class="result-summary">
                        <h3>测试完成！</h3>
                        <div class="result-stats">
                            <div class="stat-item">
                                <div class="stat-label">总题数</div>
                                <div class="stat-value">${this.answers.size}</div>
                            </div>
                            <div class="stat-item stat-correct">
                                <div class="stat-label">正确</div>
                                <div class="stat-value">${correctCount}</div>
                            </div>
                            <div class="stat-item stat-wrong">
                                <div class="stat-label">错误</div>
                                <div class="stat-value">${wrongCount}</div>
                            </div>
                            <div class="stat-item stat-accuracy">
                                <div class="stat-label">正确率</div>
                                <div class="stat-value">${accuracy}%</div>
                            </div>
                        </div>
                    </div>
                    
                    ${wrongWords.length > 0 ? `
                        <div class="wrong-words-section">
                            <h3>错词记录</h3>
                            <div class="wrong-words-list">
                                ${wrongWords.map(word => `
                                    <div class="wrong-word-item">
                                        <div class="wrong-word-header">
                                            <span class="correct-word">${word.correctAnswer}</span>
                                            <span class="word-pos ${this.getPosClass(word.part_of_speech)}">
                                                ${this.getPosLabel(word.part_of_speech)}
                                            </span>
                                        </div>
                                        <div class="wrong-word-definition">${word.definition}</div>
                                        <div class="wrong-word-answer">
                                            <span class="label">你的答案：</span>
                                            <span class="user-answer">${word.userAnswer || '(未作答)'}</span>
                                        </div>
                                    </div>
                                `).join('')}
                            </div>
                        </div>
                    ` : '<div class="perfect-score">🎉 全部正确！太棒了！</div>'}
                    
                    <div class="result-actions">
                        <button class="btn-restart-test" id="btn-restart-test">再测一次</button>
                        <button class="btn-back-home" id="btn-back-home">返回学习</button>
                    </div>
                </div>
            </div>
        `;
        
        document.getElementById('btn-restart-test').addEventListener('click', () => {
            this.renderStartScreen();
        });
        
        document.getElementById('btn-back-home').addEventListener('click', () => {
            loadModule('learn');
        });
    }
    
    async startTest() {
        const wordCount = parseInt(document.getElementById('word-count').value);
        
        if (!wordCount || wordCount < 1) {
            this.showNotification('请输入有效的单词数量', 'error');
            return;
        }
        
        try {
            const response = await fetch(`${API_BASE_URL}/api/test/start`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    user_id: getUserId(),
                    word_count: wordCount
                })
            });
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail?.message || '启动测试失败');
            }
            
            const data = await response.json();
            this.sessionId = data.session_id;
            this.words = data.words;
            this.currentWordIndex = 0;
            this.answers.clear();
            
            if (this.words.length === 0) {
                this.showNotification('没有可用的单词进行测试', 'error');
                return;
            }
            
            this.renderTestScreen();
        } catch (error) {
            this.showNotification('启动测试失败: ' + error.message, 'error');
        }
    }
    
    async submitAnswer() {
        const answerInput = document.getElementById('answer-input');
        const userAnswer = answerInput.value.trim();
        const word = this.words[this.currentWordIndex];
        
        try {
            const response = await fetch(`${API_BASE_URL}/api/test/submit`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    session_id: this.sessionId,
                    word_id: word.word_id,
                    user_answer: userAnswer
                })
            });
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail?.message || '提交答案失败');
            }
            
            const result = await response.json();
            
            // 保存答案结果
            this.answers.set(word.word_id, {
                userAnswer: userAnswer,
                isCorrect: result.is_correct,
                correctAnswer: result.correct_answer
            });
            
            // 显示即时反馈
            this.showFeedback(result.is_correct, result.correct_answer);
            
            // 禁用输入和按钮
            answerInput.disabled = true;
            document.getElementById('btn-submit-answer').disabled = true;
            
            // 2秒后进入下一题或显示结果
            setTimeout(() => {
                if (this.currentWordIndex < this.words.length - 1) {
                    this.currentWordIndex++;
                    this.renderTestScreen();
                } else {
                    this.endTest();
                }
            }, 2000);
            
        } catch (error) {
            this.showNotification('提交答案失败: ' + error.message, 'error');
        }
    }
    
    showFeedback(isCorrect, correctAnswer) {
        const feedbackArea = document.getElementById('feedback-area');
        
        if (isCorrect) {
            feedbackArea.innerHTML = `
                <div class="feedback feedback-correct">
                    <span class="feedback-icon">✓</span>
                    <span class="feedback-text">回答正确！</span>
                </div>
            `;
        } else {
            feedbackArea.innerHTML = `
                <div class="feedback feedback-wrong">
                    <span class="feedback-icon">✗</span>
                    <span class="feedback-text">回答错误</span>
                    ${correctAnswer ? `<span class="correct-answer-hint">正确答案：${correctAnswer}</span>` : ''}
                </div>
            `;
        }
    }
    
    async endTest() {
        try {
            const response = await fetch(`${API_BASE_URL}/api/test/end`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    session_id: this.sessionId
                })
            });
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail?.message || '结束测试失败');
            }
            
            // 显示结果页面
            this.renderResultScreen();
            
        } catch (error) {
            this.showNotification('结束测试失败: ' + error.message, 'error');
            // 即使API调用失败，也显示本地统计的结果
            this.renderResultScreen();
        }
    }
    
    getPosClass(pos) {
        const posMap = {
            'noun': 'pos-noun',
            'verb': 'pos-verb',
            'adj': 'pos-adj',
            'adjective': 'pos-adj',
            'adv': 'pos-adv',
            'adverb': 'pos-adv'
        };
        return posMap[pos.toLowerCase()] || 'pos-other';
    }
    
    getPosLabel(pos) {
        const labelMap = {
            'noun': '名词',
            'verb': '动词',
            'adj': '形容词',
            'adjective': '形容词',
            'adv': '副词',
            'adverb': '副词'
        };
        return labelMap[pos.toLowerCase()] || pos;
    }
    
    showNotification(message, type = 'success') {
        const notification = document.createElement('div');
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 1rem 2rem;
            background-color: ${type === 'success' ? '#4CAF50' : '#f44336'};
            color: white;
            border-radius: 4px;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
            z-index: 1000;
        `;
        notification.textContent = message;
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.remove();
        }, 3000);
    }
}

function loadTestModule(container) {
    new TestModule(container);
}

// 学习模块
class LearningModule {
    constructor(container) {
        this.container = container;
        this.words = [];
        this.currentIndex = 0;
        this.currentFilter = 'all';
        this.masteredWords = new Set();
        this.init();
    }
    
    async init() {
        this.render();
        await this.loadWords();
    }
    
    render() {
        this.container.innerHTML = `
            <div class="learn-module">
                <h2>单词学习</h2>
                
                <div class="word-display" id="word-display">
                    <div class="loading">加载中...</div>
                </div>
                
                <div class="learn-controls">
                    <button class="btn-next" id="btn-next">下一个单词</button>
                    <button class="btn-master" id="btn-master">标记已掌握</button>
                </div>
                
                <div class="word-list-section">
                    <h3>单词列表</h3>
                    <div class="word-list-filters">
                        <button class="active" data-filter="all">全部</button>
                        <button data-filter="unlearned">未学习</button>
                        <button data-filter="learned">已掌握</button>
                    </div>
                    <div class="word-list" id="word-list">
                        <div class="loading">加载中...</div>
                    </div>
                </div>
            </div>
        `;
        
        this.attachEventListeners();
    }
    
    attachEventListeners() {
        // 下一个单词按钮
        document.getElementById('btn-next').addEventListener('click', () => {
            this.loadNextWord();
        });
        
        // 标记已掌握按钮
        document.getElementById('btn-master').addEventListener('click', () => {
            this.markAsMastered();
        });
        
        // 过滤按钮
        const filterButtons = document.querySelectorAll('.word-list-filters button');
        filterButtons.forEach(button => {
            button.addEventListener('click', (e) => {
                filterButtons.forEach(btn => btn.classList.remove('active'));
                e.target.classList.add('active');
                this.currentFilter = e.target.dataset.filter;
                this.displayWordList();
            });
        });
    }
    
    async loadWords() {
        try {
            const response = await fetch(`${API_BASE_URL}/api/words`);
            if (!response.ok) {
                throw new Error('加载单词失败');
            }
            
            this.words = await response.json();
            
            if (this.words.length === 0) {
                this.displayEmptyState();
            } else {
                this.displayCurrentWord();
                this.displayWordList();
            }
        } catch (error) {
            this.displayError(error.message);
        }
    }
    
    loadNextWord() {
        if (this.words.length === 0) return;
        
        this.currentIndex = (this.currentIndex + 1) % this.words.length;
        this.displayCurrentWord();
    }
    
    displayCurrentWord() {
        if (this.words.length === 0) return;
        
        const word = this.words[this.currentIndex];
        const wordDisplay = document.getElementById('word-display');
        const isMastered = this.masteredWords.has(word.id);
        
        wordDisplay.innerHTML = `
            <h2>${word.word}</h2>
            <div class="word-definition">${word.definition}</div>
            <div class="word-meta">
                <span class="word-pos ${this.getPosClass(word.part_of_speech)}">
                    ${this.getPosLabel(word.part_of_speech)}
                </span>
                <span class="word-difficulty">难度: ${'★'.repeat(word.difficulty)}</span>
            </div>
            ${isMastered ? '<div style="margin-top: 1rem; color: #4CAF50; font-weight: bold;">✓ 已掌握</div>' : ''}
        `;
        
        // 更新按钮状态
        const masterBtn = document.getElementById('btn-master');
        masterBtn.disabled = isMastered;
    }
    
    getPosClass(pos) {
        const posMap = {
            'noun': 'pos-noun',
            'verb': 'pos-verb',
            'adj': 'pos-adj',
            'adjective': 'pos-adj',
            'adv': 'pos-adv',
            'adverb': 'pos-adv'
        };
        return posMap[pos.toLowerCase()] || 'pos-other';
    }
    
    getPosLabel(pos) {
        const labelMap = {
            'noun': '名词',
            'verb': '动词',
            'adj': '形容词',
            'adjective': '形容词',
            'adv': '副词',
            'adverb': '副词'
        };
        return labelMap[pos.toLowerCase()] || pos;
    }
    
    getColorByPartOfSpeech(pos) {
        const colorMap = {
            'noun': '#2196F3',
            'verb': '#4CAF50',
            'adj': '#FF9800',
            'adjective': '#FF9800',
            'adv': '#9C27B0',
            'adverb': '#9C27B0'
        };
        return colorMap[pos.toLowerCase()] || '#607D8B';
    }
    
    async markAsMastered() {
        if (this.words.length === 0) return;
        
        const word = this.words[this.currentIndex];
        
        try {
            const response = await fetch(
                `${API_BASE_URL}/api/words/${word.id}/master?user_id=${getUserId()}`,
                { method: 'PUT' }
            );
            
            if (!response.ok) {
                throw new Error('标记失败');
            }
            
            this.masteredWords.add(word.id);
            this.displayCurrentWord();
            this.displayWordList();
            
            // 显示成功提示
            this.showNotification('已标记为已掌握！');
        } catch (error) {
            this.showNotification('标记失败: ' + error.message, 'error');
        }
    }
    
    displayWordList() {
        const wordList = document.getElementById('word-list');
        
        let filteredWords = this.words;
        
        if (this.currentFilter === 'learned') {
            filteredWords = this.words.filter(w => this.masteredWords.has(w.id));
        } else if (this.currentFilter === 'unlearned') {
            filteredWords = this.words.filter(w => !this.masteredWords.has(w.id));
        }
        
        if (filteredWords.length === 0) {
            wordList.innerHTML = '<div class="empty-state">没有符合条件的单词</div>';
            return;
        }
        
        wordList.innerHTML = filteredWords.map((word, index) => {
            const isMastered = this.masteredWords.has(word.id);
            return `
                <div class="word-list-item ${isMastered ? 'mastered' : ''}" data-index="${this.words.indexOf(word)}">
                    <div class="word">${word.word}</div>
                    <div class="definition">${word.definition}</div>
                    <div style="margin-top: 0.5rem;">
                        <span class="word-pos ${this.getPosClass(word.part_of_speech)}" style="font-size: 0.8rem; padding: 0.25rem 0.5rem;">
                            ${this.getPosLabel(word.part_of_speech)}
                        </span>
                    </div>
                </div>
            `;
        }).join('');
        
        // 添加点击事件
        document.querySelectorAll('.word-list-item').forEach(item => {
            item.addEventListener('click', (e) => {
                const index = parseInt(e.currentTarget.dataset.index);
                this.currentIndex = index;
                this.displayCurrentWord();
                window.scrollTo({ top: 0, behavior: 'smooth' });
            });
        });
    }
    
    displayEmptyState() {
        const wordDisplay = document.getElementById('word-display');
        wordDisplay.innerHTML = `
            <div class="empty-state">
                <h3>还没有单词</h3>
                <p>请先在管理模块中添加单词</p>
            </div>
        `;
        
        document.getElementById('btn-next').disabled = true;
        document.getElementById('btn-master').disabled = true;
        
        const wordList = document.getElementById('word-list');
        wordList.innerHTML = '<div class="empty-state">还没有单词</div>';
    }
    
    displayError(message) {
        const wordDisplay = document.getElementById('word-display');
        wordDisplay.innerHTML = `
            <div class="error">
                <h3>加载失败</h3>
                <p>${message}</p>
            </div>
        `;
    }
    
    showNotification(message, type = 'success') {
        const notification = document.createElement('div');
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 1rem 2rem;
            background-color: ${type === 'success' ? '#4CAF50' : '#f44336'};
            color: white;
            border-radius: 4px;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
            z-index: 1000;
        `;
        notification.textContent = message;
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.remove();
        }, 3000);
    }
}

function loadLearningModule(container) {
    new LearningModule(container);
}

// 统计模块
class StatisticsModule {
    constructor(container) {
        this.container = container;
        this.charts = {};
        this.currentStartDate = null;
        this.currentEndDate = null;
        this.init();
    }
    
    async init() {
        this.render();
        await this.loadStatistics();
    }
    
    render() {
        // 设置默认时间范围（最近30天）
        const endDate = new Date();
        const startDate = new Date();
        startDate.setDate(startDate.getDate() - 30);
        
        this.currentStartDate = startDate.toISOString().split('T')[0];
        this.currentEndDate = endDate.toISOString().split('T')[0];
        
        this.container.innerHTML = `
            <div class="stats-module">
                <h2>学习统计</h2>
                
                <!-- 时间范围筛选器 -->
                <div class="stats-filters">
                    <div class="filter-group">
                        <label for="start-date">开始日期：</label>
                        <input type="date" id="start-date" value="${this.currentStartDate}">
                    </div>
                    <div class="filter-group">
                        <label for="end-date">结束日期：</label>
                        <input type="date" id="end-date" value="${this.currentEndDate}">
                    </div>
                    <button class="btn-apply-filter" id="btn-apply-filter">应用筛选</button>
                    <button class="btn-reset-filter" id="btn-reset-filter">重置</button>
                </div>
                
                <!-- 总体统计展示区域 -->
                <div class="overall-stats" id="overall-stats">
                    <div class="loading">加载中...</div>
                </div>
                
                <!-- 图表容器 -->
                <div class="charts-container">
                    <!-- 难度分布图表 -->
                    <div class="chart-section">
                        <h3>难度分布</h3>
                        <div class="chart-wrapper">
                            <canvas id="difficulty-chart"></canvas>
                        </div>
                    </div>
                    
                    <!-- 词性分析图表 -->
                    <div class="chart-section">
                        <h3>词性分析</h3>
                        <div class="chart-wrapper">
                            <canvas id="pos-chart"></canvas>
                        </div>
                    </div>
                    
                    <!-- 时间趋势图表 -->
                    <div class="chart-section chart-section-full">
                        <h3>学习时间趋势</h3>
                        <div class="chart-wrapper">
                            <canvas id="trend-chart"></canvas>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        this.attachEventListeners();
    }
    
    attachEventListeners() {
        // 应用筛选按钮
        document.getElementById('btn-apply-filter').addEventListener('click', () => {
            this.applyFilter();
        });
        
        // 重置按钮
        document.getElementById('btn-reset-filter').addEventListener('click', () => {
            this.resetFilter();
        });
    }
    
    async applyFilter() {
        const startDate = document.getElementById('start-date').value;
        const endDate = document.getElementById('end-date').value;
        
        if (!startDate || !endDate) {
            this.showNotification('请选择开始和结束日期', 'error');
            return;
        }
        
        if (new Date(startDate) > new Date(endDate)) {
            this.showNotification('开始日期不能晚于结束日期', 'error');
            return;
        }
        
        this.currentStartDate = startDate;
        this.currentEndDate = endDate;
        
        await this.loadStatistics();
    }
    
    resetFilter() {
        const endDate = new Date();
        const startDate = new Date();
        startDate.setDate(startDate.getDate() - 30);
        
        this.currentStartDate = startDate.toISOString().split('T')[0];
        this.currentEndDate = endDate.toISOString().split('T')[0];
        
        document.getElementById('start-date').value = this.currentStartDate;
        document.getElementById('end-date').value = this.currentEndDate;
        
        this.loadStatistics();
    }
    
    async loadStatistics() {
        await Promise.all([
            this.loadOverallStats(),
            this.loadDifficultyDistribution(),
            this.loadPosAnalysis(),
            this.loadTimeTrend()
        ]);
    }
    
    async loadOverallStats() {
        try {
            const response = await fetch(`${API_BASE_URL}/api/stats/overall?user_id=${getUserId()}`);
            
            if (!response.ok) {
                throw new Error('加载总体统计失败');
            }
            
            const stats = await response.json();
            this.displayOverallStats(stats);
        } catch (error) {
            this.displayOverallStatsError(error.message);
        }
    }
    
    displayOverallStats(stats) {
        const overallStatsDiv = document.getElementById('overall-stats');
        
        overallStatsDiv.innerHTML = `
            <div class="stat-card">
                <div class="stat-icon">📚</div>
                <div class="stat-content">
                    <div class="stat-label">总学习单词数</div>
                    <div class="stat-value">${stats.total_words || 0}</div>
                </div>
            </div>
            <div class="stat-card">
                <div class="stat-icon">✅</div>
                <div class="stat-content">
                    <div class="stat-label">已掌握数量</div>
                    <div class="stat-value">${stats.mastered_count || 0}</div>
                </div>
            </div>
            <div class="stat-card">
                <div class="stat-icon">📝</div>
                <div class="stat-content">
                    <div class="stat-label">测试次数</div>
                    <div class="stat-value">${stats.test_count || 0}</div>
                </div>
            </div>
            <div class="stat-card">
                <div class="stat-icon">🎯</div>
                <div class="stat-content">
                    <div class="stat-label">平均正确率</div>
                    <div class="stat-value">${stats.average_accuracy ? (stats.average_accuracy * 100).toFixed(1) : 0}%</div>
                </div>
            </div>
        `;
    }
    
    displayOverallStatsError(message) {
        const overallStatsDiv = document.getElementById('overall-stats');
        overallStatsDiv.innerHTML = `
            <div class="error-message">
                加载统计数据失败: ${message}
            </div>
        `;
    }
    
    async loadDifficultyDistribution() {
        try {
            const response = await fetch(`${API_BASE_URL}/api/stats/difficulty?user_id=${getUserId()}`);
            
            if (!response.ok) {
                throw new Error('加载难度分布失败');
            }
            
            const data = await response.json();
            this.renderDifficultyChart(data);
        } catch (error) {
            console.error('加载难度分布失败:', error);
            this.renderChartError('difficulty-chart', '加载难度分布失败');
        }
    }
    
    async loadPosAnalysis() {
        try {
            const response = await fetch(`${API_BASE_URL}/api/stats/pos?user_id=${getUserId()}`);
            
            if (!response.ok) {
                throw new Error('加载词性分析失败');
            }
            
            const data = await response.json();
            this.renderPosChart(data);
        } catch (error) {
            console.error('加载词性分析失败:', error);
            this.renderChartError('pos-chart', '加载词性分析失败');
        }
    }
    
    async loadTimeTrend() {
        try {
            const url = `${API_BASE_URL}/api/stats/trend?user_id=${getUserId()}&start_date=${this.currentStartDate}&end_date=${this.currentEndDate}`;
            const response = await fetch(url);
            
            if (!response.ok) {
                throw new Error('加载时间趋势失败');
            }
            
            const data = await response.json();
            this.renderTrendChart(data);
        } catch (error) {
            console.error('加载时间趋势失败:', error);
            this.renderChartError('trend-chart', '加载时间趋势失败');
        }
    }
    
    renderDifficultyChart(data) {
        // 销毁旧图表
        if (this.charts.difficulty) {
            this.charts.difficulty.destroy();
        }
        
        const ctx = document.getElementById('difficulty-chart');
        
        // 准备数据 - 后端返回的格式是 {difficulty_1: {total: x, ...}, ...}
        const labels = [];
        const values = [];
        const colors = ['#4CAF50', '#8BC34A', '#FFC107', '#FF9800', '#F44336'];
        
        // 按难度等级排序
        for (let i = 1; i <= 5; i++) {
            const key = `difficulty_${i}`;
            if (data[key]) {
                labels.push(`难度 ${i}`);
                values.push(data[key].total || 0);
            }
        }
        
        this.charts.difficulty = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: '单词数量',
                    data: values,
                    backgroundColor: colors.slice(0, values.length),
                    borderColor: colors.slice(0, values.length).map(c => c),
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return `单词数量: ${context.parsed.y}`;
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            stepSize: 1
                        }
                    }
                }
            }
        });
    }
    
    renderPosChart(data) {
        // 销毁旧图表
        if (this.charts.pos) {
            this.charts.pos.destroy();
        }
        
        const ctx = document.getElementById('pos-chart');
        
        // 准备数据 - 后端返回的格式是 {data: {noun: {total: x, ...}, ...}}
        const labels = [];
        const values = [];
        const colors = ['#2196F3', '#4CAF50', '#FF9800', '#9C27B0', '#607D8B'];
        
        const posLabels = {
            'noun': '名词',
            'verb': '动词',
            'adj': '形容词',
            'adjective': '形容词',
            'adv': '副词',
            'adverb': '副词'
        };
        
        const posData = data.data || data;
        Object.entries(posData).forEach(([pos, stats]) => {
            labels.push(posLabels[pos] || pos);
            values.push(stats.total || 0);
        });
        
        this.charts.pos = new Chart(ctx, {
            type: 'pie',
            data: {
                labels: labels,
                datasets: [{
                    data: values,
                    backgroundColor: colors.slice(0, values.length),
                    borderColor: '#fff',
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom'
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const label = context.label || '';
                                const value = context.parsed || 0;
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const percentage = ((value / total) * 100).toFixed(1);
                                return `${label}: ${value} (${percentage}%)`;
                            }
                        }
                    }
                }
            }
        });
    }
    
    renderTrendChart(data) {
        // 销毁旧图表
        if (this.charts.trend) {
            this.charts.trend.destroy();
        }
        
        const ctx = document.getElementById('trend-chart');
        
        // 准备数据 - 后端返回的格式是 {dates: [...], learned_words: [...], test_count: [...], error_count: [...]}
        const labels = data.dates || [];
        const learnedData = data.learned_words || [];
        const testedData = data.test_count || [];
        
        this.charts.trend = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: '学习单词数',
                        data: learnedData,
                        borderColor: '#4CAF50',
                        backgroundColor: 'rgba(76, 175, 80, 0.1)',
                        tension: 0.4,
                        fill: true
                    },
                    {
                        label: '测试次数',
                        data: testedData,
                        borderColor: '#2196F3',
                        backgroundColor: 'rgba(33, 150, 243, 0.1)',
                        tension: 0.4,
                        fill: true
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'top'
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            stepSize: 1
                        }
                    }
                },
                interaction: {
                    mode: 'nearest',
                    axis: 'x',
                    intersect: false
                }
            }
        });
    }
    
    renderChartError(chartId, message) {
        const canvas = document.getElementById(chartId);
        const wrapper = canvas.parentElement;
        wrapper.innerHTML = `
            <div style="display: flex; align-items: center; justify-content: center; height: 100%; color: #f44336;">
                ${message}
            </div>
        `;
    }
    
    showNotification(message, type = 'success') {
        const notification = document.createElement('div');
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 1rem 2rem;
            background-color: ${type === 'success' ? '#4CAF50' : '#f44336'};
            color: white;
            border-radius: 4px;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
            z-index: 1000;
        `;
        notification.textContent = message;
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.remove();
        }, 3000);
    }
}

function loadStatisticsModule(container) {
    new StatisticsModule(container);
}

// 管理模块
class ManagementModule {
    constructor(container) {
        this.container = container;
        this.init();
    }
    
    init() {
        this.render();
        this.attachEventListeners();
    }
    
    render() {
        this.container.innerHTML = `
            <div class="manage-module">
                <h2>单词管理</h2>
                
                <!-- 添加单词表单 -->
                <div class="manage-section">
                    <h3>添加单词</h3>
                    <form id="add-word-form" class="add-word-form">
                        <div class="form-group">
                            <label for="word-input">英文单词 *</label>
                            <input 
                                type="text" 
                                id="word-input" 
                                name="word" 
                                required 
                                placeholder="例如: hello"
                            >
                        </div>
                        
                        <div class="form-group">
                            <label for="definition-input">中文释义 *</label>
                            <input 
                                type="text" 
                                id="definition-input" 
                                name="definition" 
                                required 
                                placeholder="例如: 你好"
                            >
                        </div>
                        
                        <div class="form-row">
                            <div class="form-group">
                                <label for="pos-input">词性 *</label>
                                <select id="pos-input" name="part_of_speech" required>
                                    <option value="">请选择</option>
                                    <option value="noun">名词 (noun)</option>
                                    <option value="verb">动词 (verb)</option>
                                    <option value="adj">形容词 (adj)</option>
                                    <option value="adv">副词 (adv)</option>
                                </select>
                            </div>
                            
                            <div class="form-group">
                                <label for="difficulty-input">难度等级 *</label>
                                <select id="difficulty-input" name="difficulty" required>
                                    <option value="1">1 - 简单</option>
                                    <option value="2">2 - 较简单</option>
                                    <option value="3" selected>3 - 中等</option>
                                    <option value="4">4 - 较难</option>
                                    <option value="5">5 - 困难</option>
                                </select>
                            </div>
                        </div>
                        
                        <button type="submit" class="btn-submit">添加单词</button>
                    </form>
                </div>
                
                <!-- 批量导入 -->
                <div class="manage-section">
                    <h3>批量导入单词</h3>
                    <div class="import-section">
                        <div class="import-info">
                            <p>支持 TXT 文件格式，每行一个单词，格式如下：</p>
                            <code>单词[TAB]释义[TAB]词性[TAB]难度</code>
                            <p class="example">例如：hello	你好	noun	1</p>
                        </div>
                        
                        <div class="file-upload-area">
                            <input 
                                type="file" 
                                id="file-input" 
                                accept=".txt" 
                                style="display: none;"
                            >
                            <button class="btn-choose-file" id="btn-choose-file">
                                选择文件
                            </button>
                            <span id="file-name" class="file-name">未选择文件</span>
                            <button class="btn-upload" id="btn-upload" disabled>
                                开始导入
                            </button>
                        </div>
                        
                        <div id="import-result" class="import-result"></div>
                    </div>
                </div>
                
                <!-- MapReduce 分析 -->
                <div class="manage-section">
                    <h3>错词分析 (MapReduce)</h3>
                    <div class="mapreduce-section">
                        <p>使用 MapReduce 分析错词数据，识别高频错词模式</p>
                        <div class="mapreduce-controls">
                            <button class="btn-trigger-mapreduce" id="btn-trigger-mapreduce">
                                触发 MapReduce 分析
                            </button>
                            <button class="btn-view-results" id="btn-view-results">
                                查看分析结果
                            </button>
                        </div>
                        <div id="mapreduce-status" class="mapreduce-status"></div>
                        <div id="mapreduce-results" class="mapreduce-results"></div>
                    </div>
                </div>
                
                <!-- 默写本生成 -->
                <div class="manage-section">
                    <h3>生成默写本</h3>
                    <div class="dictation-section">
                        <p>基于 MapReduce 分析结果生成个性化默写本</p>
                        <div class="dictation-controls">
                            <div class="form-group-inline">
                                <label for="dictation-count">单词数量：</label>
                                <input 
                                    type="number" 
                                    id="dictation-count" 
                                    min="1" 
                                    max="1000" 
                                    value="50"
                                >
                            </div>
                            <div class="form-group-inline">
                                <label for="dictation-format">文件格式：</label>
                                <select id="dictation-format">
                                    <option value="txt">TXT</option>
                                    <option value="pdf">PDF</option>
                                </select>
                            </div>
                            <button class="btn-generate-dictation" id="btn-generate-dictation">
                                生成并下载
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }
    
    attachEventListeners() {
        // 添加单词表单提交
        document.getElementById('add-word-form').addEventListener('submit', (e) => {
            e.preventDefault();
            this.addWord();
        });
        
        // 文件选择
        document.getElementById('btn-choose-file').addEventListener('click', () => {
            document.getElementById('file-input').click();
        });
        
        document.getElementById('file-input').addEventListener('change', (e) => {
            const file = e.target.files[0];
            if (file) {
                document.getElementById('file-name').textContent = file.name;
                document.getElementById('btn-upload').disabled = false;
            } else {
                document.getElementById('file-name').textContent = '未选择文件';
                document.getElementById('btn-upload').disabled = true;
            }
        });
        
        // 文件上传
        document.getElementById('btn-upload').addEventListener('click', () => {
            this.uploadFile();
        });
        
        // MapReduce 触发
        document.getElementById('btn-trigger-mapreduce').addEventListener('click', () => {
            this.triggerMapReduce();
        });
        
        // 查看 MapReduce 结果
        document.getElementById('btn-view-results').addEventListener('click', () => {
            this.viewMapReduceResults();
        });
        
        // 生成默写本
        document.getElementById('btn-generate-dictation').addEventListener('click', () => {
            this.generateDictation();
        });
    }
    
    async addWord() {
        const form = document.getElementById('add-word-form');
        const formData = new FormData(form);
        
        const wordData = {
            word: formData.get('word').trim(),
            definition: formData.get('definition').trim(),
            part_of_speech: formData.get('part_of_speech'),
            difficulty: parseInt(formData.get('difficulty'))
        };
        
        // 客户端验证
        if (!wordData.word || !wordData.definition || !wordData.part_of_speech) {
            this.showNotification('请填写所有必填字段', 'error');
            return;
        }
        
        try {
            const response = await fetch(`${API_BASE_URL}/api/words`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(wordData)
            });
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail?.message || '添加单词失败');
            }
            
            const result = await response.json();
            
            // 清空表单
            form.reset();
            
            this.showNotification('单词添加成功！', 'success');
        } catch (error) {
            this.showNotification('添加失败: ' + error.message, 'error');
        }
    }
    
    async uploadFile() {
        const fileInput = document.getElementById('file-input');
        const file = fileInput.files[0];
        
        if (!file) {
            this.showNotification('请先选择文件', 'error');
            return;
        }
        
        const formData = new FormData();
        formData.append('file', file);
        
        try {
            // 显示加载状态
            const resultDiv = document.getElementById('import-result');
            resultDiv.innerHTML = '<div class="loading">正在导入...</div>';
            
            const response = await fetch(`${API_BASE_URL}/api/words/import`, {
                method: 'POST',
                body: formData
            });
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail?.message || '导入失败');
            }
            
            const result = await response.json();
            
            // 显示导入结果
            this.displayImportResult(result);
            
            // 清空文件选择
            fileInput.value = '';
            document.getElementById('file-name').textContent = '未选择文件';
            document.getElementById('btn-upload').disabled = true;
            
        } catch (error) {
            const resultDiv = document.getElementById('import-result');
            resultDiv.innerHTML = `
                <div class="result-error">
                    <h4>导入失败</h4>
                    <p>${error.message}</p>
                </div>
            `;
        }
    }
    
    displayImportResult(result) {
        const resultDiv = document.getElementById('import-result');
        
        let html = `
            <div class="result-summary">
                <h4>导入完成</h4>
                <div class="result-stats">
                    <div class="stat">
                        <span class="label">总行数：</span>
                        <span class="value">${result.total_lines}</span>
                    </div>
                    <div class="stat stat-success">
                        <span class="label">成功：</span>
                        <span class="value">${result.success_count}</span>
                    </div>
                    <div class="stat stat-failed">
                        <span class="label">失败：</span>
                        <span class="value">${result.failed_count}</span>
                    </div>
                </div>
            </div>
        `;
        
        if (result.failed_count > 0 && result.failed_lines.length > 0) {
            html += `
                <div class="failed-lines">
                    <h5>失败详情：</h5>
                    <ul>
                        ${result.failed_lines.map(item => `
                            <li>
                                <strong>行 ${item.line_number}:</strong> ${item.error}
                                ${item.content ? `<br><code>${item.content}</code>` : ''}
                            </li>
                        `).join('')}
                    </ul>
                </div>
            `;
        }
        
        resultDiv.innerHTML = html;
    }
    
    async triggerMapReduce() {
        try {
            const statusDiv = document.getElementById('mapreduce-status');
            statusDiv.innerHTML = '<div class="loading">正在启动 MapReduce 分析...</div>';
            
            const response = await fetch(`${API_BASE_URL}/api/mapreduce/trigger?user_id=${getUserId()}`, {
                method: 'POST'
            });
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail?.message || '触发分析失败');
            }
            
            const result = await response.json();
            
            statusDiv.innerHTML = `
                <div class="status-success">
                    <p>✓ ${result.message}</p>
                    <p class="job-id">作业ID: ${result.job_id}</p>
                </div>
            `;
            
            // 保存 job_id 以便后续查询
            this.currentJobId = result.job_id;
            
            // 自动查询状态
            this.pollJobStatus(result.job_id);
            
        } catch (error) {
            const statusDiv = document.getElementById('mapreduce-status');
            statusDiv.innerHTML = `
                <div class="status-error">
                    <p>✗ 触发失败: ${error.message}</p>
                </div>
            `;
        }
    }
    
    async pollJobStatus(jobId, attempts = 0) {
        if (attempts >= 10) {
            // 最多轮询10次
            return;
        }
        
        try {
            const response = await fetch(`${API_BASE_URL}/api/mapreduce/status/${jobId}`);
            
            if (!response.ok) {
                return;
            }
            
            const status = await response.json();
            const statusDiv = document.getElementById('mapreduce-status');
            
            if (status.status === 'completed') {
                statusDiv.innerHTML = `
                    <div class="status-success">
                        <p>✓ 分析完成！</p>
                        <p class="job-id">作业ID: ${jobId}</p>
                    </div>
                `;
                this.showNotification('MapReduce 分析完成', 'success');
            } else if (status.status === 'failed') {
                statusDiv.innerHTML = `
                    <div class="status-error">
                        <p>✗ 分析失败</p>
                        <p>${status.error || '未知错误'}</p>
                    </div>
                `;
            } else if (status.status === 'running') {
                statusDiv.innerHTML = `
                    <div class="status-running">
                        <p>⏳ 分析进行中...</p>
                        <p class="job-id">作业ID: ${jobId}</p>
                    </div>
                `;
                // 3秒后再次查询
                setTimeout(() => this.pollJobStatus(jobId, attempts + 1), 3000);
            }
        } catch (error) {
            console.error('查询作业状态失败:', error);
        }
    }
    
    async viewMapReduceResults() {
        try {
            const resultsDiv = document.getElementById('mapreduce-results');
            resultsDiv.innerHTML = '<div class="loading">正在加载结果...</div>';
            
            const response = await fetch(`${API_BASE_URL}/api/mapreduce/results?user_id=${getUserId()}&top_n=20`);
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail?.message || '获取结果失败');
            }
            
            const data = await response.json();
            
            if (data.results.length === 0) {
                resultsDiv.innerHTML = `
                    <div class="empty-state">
                        <p>暂无分析结果</p>
                        <p>请先触发 MapReduce 分析</p>
                    </div>
                `;
                return;
            }
            
            resultsDiv.innerHTML = `
                <div class="results-container">
                    <h4>高频错词 Top ${data.results.length}</h4>
                    <div class="results-table">
                        <table>
                            <thead>
                                <tr>
                                    <th>排名</th>
                                    <th>单词</th>
                                    <th>释义</th>
                                    <th>词性</th>
                                    <th>错误次数</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${data.results.map((word, index) => `
                                    <tr>
                                        <td>${index + 1}</td>
                                        <td class="word-cell">${word.word}</td>
                                        <td>${word.definition}</td>
                                        <td>
                                            <span class="word-pos ${this.getPosClass(word.part_of_speech)}">
                                                ${this.getPosLabel(word.part_of_speech)}
                                            </span>
                                        </td>
                                        <td class="error-count">${word.error_count}</td>
                                    </tr>
                                `).join('')}
                            </tbody>
                        </table>
                    </div>
                    <p class="total-info">共 ${data.total_count} 个错词</p>
                </div>
            `;
            
        } catch (error) {
            const resultsDiv = document.getElementById('mapreduce-results');
            resultsDiv.innerHTML = `
                <div class="result-error">
                    <p>获取结果失败: ${error.message}</p>
                </div>
            `;
        }
    }
    
    async generateDictation() {
        const topN = parseInt(document.getElementById('dictation-count').value);
        const format = document.getElementById('dictation-format').value;
        
        if (!topN || topN < 1) {
            this.showNotification('请输入有效的单词数量', 'error');
            return;
        }
        
        try {
            this.showNotification('正在生成默写本...', 'success');
            
            const url = `${API_BASE_URL}/api/dictation/generate?user_id=${getUserId()}&top_n=${topN}&format=${format}`;
            
            const response = await fetch(url, {
                method: 'POST'
            });
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail?.message || '生成失败');
            }
            
            // 获取文件内容
            const blob = await response.blob();
            
            // 创建下载链接
            const downloadUrl = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = downloadUrl;
            a.download = `dictation_book_${getUserId()}.${format}`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(downloadUrl);
            
            this.showNotification('默写本生成成功！', 'success');
            
        } catch (error) {
            this.showNotification('生成失败: ' + error.message, 'error');
        }
    }
    
    getPosClass(pos) {
        const posMap = {
            'noun': 'pos-noun',
            'verb': 'pos-verb',
            'adj': 'pos-adj',
            'adjective': 'pos-adj',
            'adv': 'pos-adv',
            'adverb': 'pos-adv'
        };
        return posMap[pos.toLowerCase()] || 'pos-other';
    }
    
    getPosLabel(pos) {
        const labelMap = {
            'noun': '名词',
            'verb': '动词',
            'adj': '形容词',
            'adjective': '形容词',
            'adv': '副词',
            'adverb': '副词'
        };
        return labelMap[pos.toLowerCase()] || pos;
    }
    
    showNotification(message, type = 'success') {
        const notification = document.createElement('div');
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 1rem 2rem;
            background-color: ${type === 'success' ? '#4CAF50' : '#f44336'};
            color: white;
            border-radius: 4px;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
            z-index: 1000;
        `;
        notification.textContent = message;
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.remove();
        }, 3000);
    }
}

function loadManagementModule(container) {
    new ManagementModule(container);
}

// 复习模块
class ReviewModule {
    constructor(container) {
        this.container = container;
        this.reviewQueue = [];
        this.currentIndex = 0;
        this.init();
    }
    
    async init() {
        this.render();
        await this.loadReviewQueue();
    }
    
    render() {
        this.container.innerHTML = `
            <div class="review-module">
                <h2>单词复习</h2>
                
                <div class="review-display" id="review-display">
                    <div class="loading">加载中...</div>
                </div>
                
                <div class="review-controls" id="review-controls" style="display: none;">
                    <div class="answer-input-area">
                        <input 
                            type="text" 
                            id="review-answer-input" 
                            class="answer-input" 
                            placeholder="输入英文单词..."
                            autocomplete="off"
                        >
                        <button class="btn-submit-answer" id="btn-submit-review">提交答案</button>
                    </div>
                    <div class="feedback-area" id="review-feedback-area"></div>
                </div>
            </div>
        `;
        
        this.attachEventListeners();
    }
    
    attachEventListeners() {
        const answerInput = document.getElementById('review-answer-input');
        const submitBtn = document.getElementById('btn-submit-review');
        
        if (answerInput) {
            // 回车提交
            answerInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    this.submitAnswer();
                }
            });
        }
        
        if (submitBtn) {
            submitBtn.addEventListener('click', () => {
                this.submitAnswer();
            });
        }
    }
    
    async loadReviewQueue() {
        try {
            const response = await fetch(`${API_BASE_URL}/api/review/queue?user_id=${getUserId()}`);
            
            if (!response.ok) {
                throw new Error('加载复习队列失败');
            }
            
            this.reviewQueue = await response.json();
            
            if (this.reviewQueue.length === 0) {
                this.displayEmptyState();
            } else {
                this.displayCurrentWord();
                document.getElementById('review-controls').style.display = 'block';
            }
        } catch (error) {
            this.displayError(error.message);
        }
    }
    
    displayCurrentWord() {
        if (this.reviewQueue.length === 0) return;
        
        const word = this.reviewQueue[this.currentIndex];
        const reviewDisplay = document.getElementById('review-display');
        
        // 格式化上次复习时间
        let lastReviewText = '从未复习';
        if (word.last_review_time) {
            const lastReviewDate = new Date(word.last_review_time);
            lastReviewText = lastReviewDate.toLocaleString('zh-CN');
        }
        
        reviewDisplay.innerHTML = `
            <div class="review-card">
                <div class="review-progress">
                    <span>进度: ${this.currentIndex + 1} / ${this.reviewQueue.length}</span>
                </div>
                
                <div class="review-info">
                    <div class="info-item">
                        <span class="info-label">错误次数：</span>
                        <span class="info-value error-count">${word.error_count}</span>
                    </div>
                    <div class="info-item">
                        <span class="info-label">上次复习：</span>
                        <span class="info-value">${lastReviewText}</span>
                    </div>
                </div>
                
                <div class="question-card">
                    <div class="question-label">请输入对应的英文单词：</div>
                    <div class="question-definition">${word.definition}</div>
                    <div class="question-meta">
                        <span class="word-pos ${this.getPosClass(word.part_of_speech)}">
                            ${this.getPosLabel(word.part_of_speech)}
                        </span>
                        <span class="word-difficulty">难度: ${'★'.repeat(word.difficulty)}</span>
                    </div>
                </div>
            </div>
        `;
        
        // 清空输入框和反馈
        const answerInput = document.getElementById('review-answer-input');
        if (answerInput) {
            answerInput.value = '';
            answerInput.disabled = false;
            answerInput.focus();
        }
        
        const submitBtn = document.getElementById('btn-submit-review');
        if (submitBtn) {
            submitBtn.disabled = false;
        }
        
        const feedbackArea = document.getElementById('review-feedback-area');
        if (feedbackArea) {
            feedbackArea.innerHTML = '';
        }
    }
    
    async submitAnswer() {
        const answerInput = document.getElementById('review-answer-input');
        const userAnswer = answerInput.value.trim();
        const word = this.reviewQueue[this.currentIndex];
        
        if (!userAnswer) {
            this.showNotification('请输入答案', 'error');
            return;
        }
        
        try {
            const response = await fetch(`${API_BASE_URL}/api/review/submit`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    user_id: getUserId(),
                    word_id: word.word_id,
                    user_answer: userAnswer
                })
            });
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || '提交答案失败');
            }
            
            const result = await response.json();
            
            // 显示即时反馈
            this.showFeedback(result.is_correct, result.correct_answer);
            
            // 禁用输入和按钮
            answerInput.disabled = true;
            document.getElementById('btn-submit-review').disabled = true;
            
            // 2秒后进入下一题或完成复习
            setTimeout(() => {
                if (this.currentIndex < this.reviewQueue.length - 1) {
                    this.currentIndex++;
                    this.displayCurrentWord();
                } else {
                    this.displayCompletionScreen();
                }
            }, 2000);
            
        } catch (error) {
            this.showNotification('提交答案失败: ' + error.message, 'error');
        }
    }
    
    showFeedback(isCorrect, correctAnswer) {
        const feedbackArea = document.getElementById('review-feedback-area');
        
        if (isCorrect) {
            feedbackArea.innerHTML = `
                <div class="feedback feedback-correct">
                    <span class="feedback-icon">✓</span>
                    <span class="feedback-text">回答正确！</span>
                </div>
            `;
        } else {
            feedbackArea.innerHTML = `
                <div class="feedback feedback-wrong">
                    <span class="feedback-icon">✗</span>
                    <span class="feedback-text">回答错误</span>
                    ${correctAnswer ? `<span class="correct-answer-hint">正确答案：${correctAnswer}</span>` : ''}
                </div>
            `;
        }
    }
    
    displayCompletionScreen() {
        const reviewDisplay = document.getElementById('review-display');
        
        reviewDisplay.innerHTML = `
            <div class="review-completion">
                <h3>🎉 复习完成！</h3>
                <p>你已经完成了所有需要复习的单词</p>
                <div class="completion-actions">
                    <button class="btn-restart-review" id="btn-restart-review">重新复习</button>
                    <button class="btn-back-home" id="btn-back-home">返回学习</button>
                </div>
            </div>
        `;
        
        document.getElementById('review-controls').style.display = 'none';
        
        document.getElementById('btn-restart-review').addEventListener('click', () => {
            this.currentIndex = 0;
            this.displayCurrentWord();
            document.getElementById('review-controls').style.display = 'block';
        });
        
        document.getElementById('btn-back-home').addEventListener('click', () => {
            loadModule('learn');
        });
    }
    
    displayEmptyState() {
        const reviewDisplay = document.getElementById('review-display');
        reviewDisplay.innerHTML = `
            <div class="empty-state">
                <h3>暂无需要复习的单词</h3>
                <p>你还没有错词记录，或者所有单词都已经掌握了！</p>
                <button class="btn-back-home" id="btn-back-home">返回学习</button>
            </div>
        `;
        
        document.getElementById('btn-back-home').addEventListener('click', () => {
            loadModule('learn');
        });
    }
    
    displayError(message) {
        const reviewDisplay = document.getElementById('review-display');
        reviewDisplay.innerHTML = `
            <div class="error">
                <h3>加载失败</h3>
                <p>${message}</p>
                <button class="btn-back-home" id="btn-back-home">返回学习</button>
            </div>
        `;
        
        document.getElementById('btn-back-home').addEventListener('click', () => {
            loadModule('learn');
        });
    }
    
    getPosClass(pos) {
        const posMap = {
            'noun': 'pos-noun',
            'verb': 'pos-verb',
            'adj': 'pos-adj',
            'adjective': 'pos-adj',
            'adv': 'pos-adv',
            'adverb': 'pos-adv'
        };
        return posMap[pos.toLowerCase()] || 'pos-other';
    }
    
    getPosLabel(pos) {
        const labelMap = {
            'noun': '名词',
            'verb': '动词',
            'adj': '形容词',
            'adjective': '形容词',
            'adv': '副词',
            'adverb': '副词'
        };
        return labelMap[pos.toLowerCase()] || pos;
    }
    
    showNotification(message, type = 'success') {
        const notification = document.createElement('div');
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 1rem 2rem;
            background-color: ${type === 'success' ? '#4CAF50' : '#f44336'};
            color: white;
            border-radius: 4px;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
            z-index: 1000;
        `;
        notification.textContent = message;
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.remove();
        }, 3000);
    }
}

function loadReviewModule(container) {
    new ReviewModule(container);
}

// 初始化
initUserSwitcher();
loadModule('learn');
