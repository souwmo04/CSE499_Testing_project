/**
 * VLM Interface - AI Dashboard Assistant
 * =======================================
 * 
 * This module handles the frontend interaction with the VLM (Vision-Language Model)
 * backend powered by Ollama + LLaVA.
 * 
 * Features:
 * - Real-time AI chat about dashboard data
 * - Status checking for Ollama availability
 * - Loading states and error handling
 * - Response formatting
 * 
 * Algorithm: Visual-Time-Series Reasoning Pipeline (Frontend Part)
 * 1. Capture user question
 * 2. Send to /vlm/chat/ endpoint with CSRF token
 * 3. Display loading state during VLM processing
 * 4. Render AI response with formatting
 * 5. Handle errors gracefully
 */

document.addEventListener('DOMContentLoaded', function() {
    // DOM Elements
    const askBtn = document.getElementById('ask-ai-btn');
    const questionInput = document.getElementById('ai-question');
    const answerBox = document.getElementById('ai-answer');
    const statusDot = document.querySelector('.status-dot');
    const statusText = document.querySelector('.status-text');
    const aiContainer = document.querySelector('.ai-container');
    const aiMediaFrame = document.getElementById('ai-media-frame');
    
    // State
    let isProcessing = false;
    let vlmStatus = 'unknown';
    
    // =========================================================================
    // CSRF TOKEN HELPER
    // =========================================================================
    function getCSRFToken() {
        // Try to get from form first
        const tokenInput = document.querySelector('[name=csrfmiddlewaretoken]');
        if (tokenInput) return tokenInput.value;
        
        // Fallback to cookie
        const cookie = document.cookie.split(';').find(c => c.trim().startsWith('csrftoken='));
        return cookie ? cookie.split('=')[1] : '';
    }
    
    // =========================================================================
    // VLM STATUS CHECK
    // =========================================================================
    async function checkVLMStatus() {
        try {
            const response = await fetch('/vlm/status/', {
                method: 'GET',
                headers: { 'Accept': 'application/json' }
            });
            
            const data = await response.json();
            vlmStatus = data.status;
            
            updateStatusDisplay(data.status, data.message);
            return data.status === 'online';
            
        } catch (error) {
            console.error('VLM status check failed:', error);
            updateStatusDisplay('offline', 'Cannot connect to AI service');
            return false;
        }
    }
    
    function updateStatusDisplay(status, message) {
        if (!statusDot || !statusText) return;
        
        statusDot.className = 'status-dot';
        
        if (status === 'online') {
            statusDot.classList.add('online');
            statusText.textContent = 'Online';
            statusText.style.color = '#10b981';
        } else if (status === 'offline') {
            statusDot.classList.add('offline');
            statusText.textContent = 'Offline';
            statusText.style.color = '#ef4444';
        } else {
            statusDot.classList.add('checking');
            statusText.textContent = 'Checking...';
            statusText.style.color = '#f59e0b';
        }
    }
    
    // =========================================================================
    // DISPLAY FUNCTIONS
    // =========================================================================
    function showLoading() {
        if (!answerBox) return;
        
        answerBox.innerHTML = `
            <div class="ai-loading">
                <div class="loading-spinner"></div>
                <div class="loading-content">
                    <h4>Analyzing dashboard snapshot...</h4>
                    <p>The AI is examining charts, trends, and patterns. This may take 10-30 seconds.</p>
                </div>
            </div>
        `;
        
        // Add loading styles if not present
        if (!document.getElementById('vlm-loading-styles')) {
            const styles = document.createElement('style');
            styles.id = 'vlm-loading-styles';
            styles.textContent = `
                .ai-loading {
                    display: flex;
                    align-items: flex-start;
                    gap: 16px;
                    padding: 20px;
                    background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
                    border-radius: 12px;
                    border: 1px solid #e2e8f0;
                }
                
                .loading-spinner {
                    width: 40px;
                    height: 40px;
                    border: 3px solid #e2e8f0;
                    border-top-color: #667eea;
                    border-radius: 50%;
                    animation: spin 1s linear infinite;
                    flex-shrink: 0;
                }
                
                @keyframes spin {
                    to { transform: rotate(360deg); }
                }
                
                .loading-content h4 {
                    font-size: 16px;
                    font-weight: 600;
                    color: #1e293b;
                    margin-bottom: 6px;
                }
                
                .loading-content p {
                    font-size: 14px;
                    color: #64748b;
                }
                
                .ai-response {
                    padding: 20px;
                    background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
                    border-radius: 12px;
                    border: 1px solid #e2e8f0;
                }
                
                .ai-response-header {
                    display: flex;
                    align-items: center;
                    gap: 10px;
                    margin-bottom: 14px;
                    padding-bottom: 12px;
                    border-bottom: 1px solid #e2e8f0;
                }
                
                .ai-response-icon {
                    font-size: 24px;
                }
                
                .ai-response-title {
                    font-size: 15px;
                    font-weight: 600;
                    color: #667eea;
                }
                
                .ai-response-text {
                    font-size: 15px;
                    line-height: 1.7;
                    color: #334155;
                    white-space: pre-wrap;
                }
                
                .ai-error {
                    padding: 20px;
                    background: linear-gradient(135deg, #fef2f2 0%, #fee2e2 100%);
                    border-radius: 12px;
                    border: 1px solid #fecaca;
                }
                
                .ai-error-header {
                    display: flex;
                    align-items: center;
                    gap: 10px;
                    margin-bottom: 12px;
                }
                
                .ai-error-icon {
                    font-size: 24px;
                }
                
                .ai-error-title {
                    font-size: 15px;
                    font-weight: 600;
                    color: #dc2626;
                }
                
                .ai-error-text {
                    font-size: 14px;
                    color: #991b1b;
                    margin-bottom: 12px;
                }
                
                .ai-error-help {
                    font-size: 13px;
                    color: #7f1d1d;
                    background: rgba(255, 255, 255, 0.5);
                    padding: 10px;
                    border-radius: 8px;
                }
                
                .status-dot {
                    width: 10px;
                    height: 10px;
                    border-radius: 50%;
                    background: #94a3b8;
                }
                
                .status-dot.online {
                    background: #10b981;
                    box-shadow: 0 0 8px rgba(16, 185, 129, 0.5);
                }
                
                .status-dot.offline {
                    background: #ef4444;
                    box-shadow: 0 0 8px rgba(239, 68, 68, 0.5);
                }
                
                .status-dot.checking {
                    background: #f59e0b;
                    animation: pulse-status 1.5s ease-in-out infinite;
                }
                
                @keyframes pulse-status {
                    0%, 100% { opacity: 1; }
                    50% { opacity: 0.5; }
                }
            `;
            document.head.appendChild(styles);
        }
    }
    
    function showResponse(response, model) {
        if (!answerBox) return;
        
        const modelInfo = model ? ` (${model})` : '';
        
        answerBox.innerHTML = `
            <div class="ai-response">
                <div class="ai-response-header">
                    <span class="ai-response-icon">🤖</span>
                    <span class="ai-response-title">AI Analysis${modelInfo}</span>
                </div>
                <div class="ai-response-text">${escapeHtml(response)}</div>
            </div>
        `;
    }
    
    function showError(error, isOffline = false) {
        if (!answerBox) return;
        
        const helpText = isOffline 
            ? 'Make sure Ollama is running: <code>ollama serve</code><br>And LLaVA is installed: <code>ollama pull llava</code>'
            : 'Please check your connection and try again.';
        
        answerBox.innerHTML = `
            <div class="ai-error">
                <div class="ai-error-header">
                    <span class="ai-error-icon">⚠️</span>
                    <span class="ai-error-title">${isOffline ? 'AI Service Offline' : 'Error'}</span>
                </div>
                <p class="ai-error-text">${escapeHtml(error)}</p>
                <div class="ai-error-help">${helpText}</div>
            </div>
        `;
    }
    
    function showPlaceholder() {
        if (!answerBox) return;
        
        answerBox.innerHTML = `
            <div class="ai-placeholder">
                <div class="placeholder-icon">💡</div>
                <div class="placeholder-content">
                    <h4>Ready to help!</h4>
                    <p>Ask a question to analyze the latest dashboard snapshot.</p>
                </div>
            </div>
        `;
    }

    function showSnapshotReady() {
        if (!answerBox) return;

        answerBox.innerHTML = `
            <div class="ai-placeholder">
                <div class="placeholder-icon">📸</div>
                <div class="placeholder-content">
                    <h4>Snapshot ready</h4>
                    <p>Now ask a question about this snapshot.</p>
                </div>
            </div>
        `;
    }
    
    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    // =========================================================================
    // MAIN CHAT FUNCTION
    // =========================================================================
    async function askAI() {
        if (isProcessing) return;
        
        const question = questionInput?.value?.trim();
        
        if (!question) {
            showPlaceholder();
            return;
        }
        
        isProcessing = true;
        updateAskButtonState();
        
        showLoading();
        
        const snapshotId = aiContainer?.dataset?.snapshotId;

        try {
            const response = await fetch('/vlm/chat/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCSRFToken()
                },
                body: JSON.stringify({
                    question: question,
                    snapshot_id: snapshotId || null
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                showResponse(data.answer, data.model);
            } else {
                const isOffline = data.error?.includes('Cannot connect') || 
                                  data.error?.includes('not running') ||
                                  data.error?.includes('Ollama');
                showError(data.error || 'Unknown error occurred', isOffline);
                
                // Update status if offline
                if (isOffline) {
                    updateStatusDisplay('offline', data.error);
                }
            }
            
        } catch (error) {
            console.error('VLM chat error:', error);
            showError('Network error: ' + error.message, true);
            updateStatusDisplay('offline', 'Connection failed');
        } finally {
            isProcessing = false;
            updateAskButtonState();
        }
    }
    
    // =========================================================================
    // EVENT LISTENERS
    // =========================================================================
    function updateAskButtonState() {
        if (!askBtn || !questionInput) return;

        const question = questionInput.value.trim();
        const isValid = question.length >= 3;

        askBtn.disabled = !isValid || isProcessing;
        askBtn.classList.toggle('ai-btn-disabled', !isValid || isProcessing);
    }

    function initSnapshotPreview() {
        const imageEl = document.getElementById('ai-media-image');
        if (!imageEl || !aiMediaFrame) return;

        imageEl.addEventListener('error', () => {
            aiMediaFrame.innerHTML = `
                <div class="ai-media-empty">
                    <div class="ai-media-empty-title">Snapshot unavailable</div>
                    <div class="ai-media-empty-text">Save a new snapshot to enable visual analysis.</div>
                </div>
            `;
        }, { once: true });
    }

    if (askBtn) {
        askBtn.addEventListener('click', askAI);
    }
    
    if (questionInput) {
        questionInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                askAI();
            }
        });

        questionInput.addEventListener('input', updateAskButtonState);
    }
    
    // =========================================================================
    // INITIALIZATION
    // =========================================================================
    // Check VLM status on page load
    checkVLMStatus();

    initSnapshotPreview();
    updateAskButtonState();

    window.addEventListener('snapshot:saved', (e) => {
        const snapshotId = e?.detail?.snapshotId;
        if (aiContainer && snapshotId) {
            aiContainer.dataset.snapshotId = snapshotId;
        }

        showSnapshotReady();
        updateAskButtonState();
    });
    
    // Re-check status every 30 seconds
    setInterval(checkVLMStatus, 30000);
    
    // Expose functions globally for debugging
    window.vlmInterface = {
        checkStatus: checkVLMStatus,
        askAI: askAI,
        getStatus: () => vlmStatus
    };
});
