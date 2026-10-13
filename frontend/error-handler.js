/**
 * 前端错误处理工具
 * 提供统一的错误处理和用户反馈机制
 */

class ErrorHandler {
    /**
     * 处理 API 错误响应
     * @param {Response} response - Fetch API 响应对象
     * @returns {Promise<Error>} - 格式化的错误对象
     */
    static async handleApiError(response) {
        let errorMessage = '请求失败';
        let errorCode = 'UNKNOWN_ERROR';
        let errorDetails = [];
        
        try {
            const errorData = await response.json();
            
            if (errorData.error) {
                errorCode = errorData.error.code || errorCode;
                errorMessage = errorData.error.message || errorMessage;
                errorDetails = errorData.error.details || [];
            } else if (errorData.detail) {
                // 兼容旧格式
                if (typeof errorData.detail === 'string') {
                    errorMessage = errorData.detail;
                } else if (errorData.detail.message) {
                    errorMessage = errorData.detail.message;
                    errorCode = errorData.detail.code || errorCode;
                    errorDetails = errorData.detail.details || [];
                }
            }
        } catch (e) {
            // 如果无法解析 JSON，使用默认错误消息
            errorMessage = `HTTP ${response.status}: ${response.statusText}`;
        }
        
        const error = new Error(errorMessage);
        error.code = errorCode;
        error.details = errorDetails;
        error.status = response.status;
        
        return error;
    }
    
    /**
     * 处理网络错误
     * @param {Error} error - 网络错误对象
     * @returns {Error} - 格式化的错误对象
     */
    static handleNetworkError(error) {
        const formattedError = new Error('网络连接失败，请检查网络设置');
        formattedError.code = 'NETWORK_ERROR';
        formattedError.details = [{ error: error.message }];
        formattedError.originalError = error;
        
        return formattedError;
    }
    
    /**
     * 显示错误通知
     * @param {string} message - 错误消息
     * @param {string} type - 通知类型 ('error', 'warning', 'info')
     * @param {number} duration - 显示时长（毫秒）
     */
    static showNotification(message, type = 'error', duration = 3000) {
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        
        const colors = {
            'error': '#f44336',
            'warning': '#ff9800',
            'info': '#2196F3',
            'success': '#4CAF50'
        };
        
        const icons = {
            'error': '✗',
            'warning': '⚠',
            'info': 'ℹ',
            'success': '✓'
        };
        
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 1rem 2rem;
            background-color: ${colors[type] || colors.error};
            color: white;
            border-radius: 4px;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
            z-index: 10000;
            display: flex;
            align-items: center;
            gap: 0.5rem;
            max-width: 400px;
            animation: slideIn 0.3s ease-out;
        `;
        
        notification.innerHTML = `
            <span style="font-size: 1.2rem;">${icons[type] || icons.error}</span>
            <span>${message}</span>
        `;
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.style.animation = 'slideOut 0.3s ease-in';
            setTimeout(() => {
                notification.remove();
            }, 300);
        }, duration);
    }
    
    /**
     * 显示详细错误信息（用于调试）
     * @param {Error} error - 错误对象
     */
    static showDetailedError(error) {
        console.error('Detailed Error:', {
            message: error.message,
            code: error.code,
            status: error.status,
            details: error.details
        });
        
        // 在开发环境显示详细错误
        if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
            let detailsHtml = '';
            if (error.details && error.details.length > 0) {
                detailsHtml = '<ul style="margin-top: 0.5rem; padding-left: 1.5rem;">';
                error.details.forEach(detail => {
                    if (detail.field) {
                        detailsHtml += `<li><strong>${detail.field}:</strong> ${detail.message}</li>`;
                    } else {
                        detailsHtml += `<li>${JSON.stringify(detail)}</li>`;
                    }
                });
                detailsHtml += '</ul>';
            }
            
            const errorModal = document.createElement('div');
            errorModal.style.cssText = `
                position: fixed;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                background: white;
                padding: 2rem;
                border-radius: 8px;
                box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3);
                z-index: 10001;
                max-width: 600px;
                max-height: 80vh;
                overflow-y: auto;
                color: #333;
            `;
            
            errorModal.innerHTML = `
                <h3 style="margin-top: 0; color: #f44336;">错误详情</h3>
                <p><strong>错误代码:</strong> ${error.code || 'N/A'}</p>
                <p><strong>HTTP 状态:</strong> ${error.status || 'N/A'}</p>
                <p><strong>错误消息:</strong> ${error.message}</p>
                ${detailsHtml}
                <button onclick="this.parentElement.remove()" style="
                    margin-top: 1rem;
                    padding: 0.5rem 1rem;
                    background: #2196F3;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    cursor: pointer;
                ">关闭</button>
            `;
            
            document.body.appendChild(errorModal);
        }
    }
    
    /**
     * 通用 API 调用包装器
     * @param {Function} apiCall - API 调用函数
     * @param {Object} options - 选项
     * @returns {Promise} - API 响应
     */
    static async withErrorHandling(apiCall, options = {}) {
        const {
            showNotification = true,
            showDetails = false,
            customErrorMessage = null
        } = options;
        
        try {
            const response = await apiCall();
            
            if (!response.ok) {
                const error = await this.handleApiError(response);
                
                if (showNotification) {
                    this.showNotification(customErrorMessage || error.message, 'error');
                }
                
                if (showDetails) {
                    this.showDetailedError(error);
                }
                
                throw error;
            }
            
            return response;
        } catch (error) {
            // 处理网络错误
            if (error.name === 'TypeError' && error.message.includes('fetch')) {
                const networkError = this.handleNetworkError(error);
                
                if (showNotification) {
                    this.showNotification(networkError.message, 'error');
                }
                
                throw networkError;
            }
            
            // 重新抛出已处理的错误
            throw error;
        }
    }
}

// 添加 CSS 动画
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(400px);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(400px);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);

// 导出为全局对象
window.ErrorHandler = ErrorHandler;
