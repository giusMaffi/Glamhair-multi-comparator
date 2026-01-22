/**
 * Glamhair Chat Application
 * Frontend chat interface with real-time messaging
 */

class ChatApp {
    constructor() {
        this.baseUrl = window.location.origin;
        this.sessionId = null;
        
        // DOM elements
        this.messagesContainer = document.getElementById('messages');
        this.userInput = document.getElementById('user-input');
        this.sendButton = document.getElementById('send-button');
        this.statusIndicator = document.querySelector('.status-indicator');
        this.statusText = document.querySelector('.status-text');
        this.sessionIdDisplay = document.getElementById('session-id');
        
        // Event listeners
        this.sendButton.addEventListener('click', () => this.sendMessage());
        this.userInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });
        
        // Auto-resize textarea
        this.userInput.addEventListener('input', () => {
            this.userInput.style.height = 'auto';
            this.userInput.style.height = this.userInput.scrollHeight + 'px';
        });
        
        // Initialize session
        this.initSession();
    }
    
    async initSession() {
        this.updateStatus('connecting', 'Connessione in corso...');
        
        try {
            const response = await fetch(`${this.baseUrl}/api/session/start`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            if (!response.ok) {
                throw new Error('Failed to start session');
            }
            
            const data = await response.json();
            this.sessionId = data.session_id;
            
            // Display session ID (first 8 chars)
            if (this.sessionIdDisplay) {
                this.sessionIdDisplay.textContent = this.sessionId.substring(0, 8) + '...';
            }
            
            this.updateStatus('connected', 'Connesso');
            this.userInput.disabled = false;
            this.sendButton.disabled = false;
            this.userInput.focus();
            
        } catch (error) {
            console.error('Error initializing session:', error);
            this.updateStatus('error', 'Errore connessione');
            alert('Impossibile connettersi al server. Ricarica la pagina.');
        }
    }
    
    updateStatus(type, text) {
        this.statusIndicator.className = 'status-indicator ' + type;
        this.statusText.textContent = text;
    }
    
    async sendMessage() {
        const message = this.userInput.value.trim();
        
        if (!message) return;
        if (!this.sessionId) {
            alert('Session not ready. Please wait...');
            return;
        }
        
        // CRITICAL: Add user message to UI FIRST (before API call)
        this.addMessage('user', message);
        
        // Clear input and disable
        this.userInput.value = '';
        this.userInput.style.height = 'auto';
        this.userInput.disabled = true;
        this.sendButton.disabled = true;
        
        // Show loading indicator
        const loadingId = this.addMessage('loading', 'Sto pensando...');
        
        try {
            const response = await fetch(`${this.baseUrl}/api/chat`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    session_id: this.sessionId,
                    message: message
                })
            });
            
            // Remove loading message
            this.removeMessage(loadingId);
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || 'Request failed');
            }
            
            const data = await response.json();
            
            // Add assistant response
            this.addMessage('assistant', data.response);
            
        } catch (error) {
            console.error('Error sending message:', error);
            this.removeMessage(loadingId);
            this.addMessage('assistant', `❌ Errore: ${error.message}`);
        } finally {
            // Re-enable input
            this.userInput.disabled = false;
            this.sendButton.disabled = false;
            this.userInput.focus();
        }
    }
    
    addMessage(role, content) {
        const messageId = 'msg-' + Date.now() + '-' + Math.random().toString(36).substr(2, 9);
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${role}`;
        messageDiv.id = messageId;
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        
        if (role === 'loading') {
            contentDiv.innerHTML = '<span class="loading-dots">Sto pensando...</span>';
        } else {
            // Convert markdown-like formatting to HTML
            let formattedContent = this.formatMessage(content);
            contentDiv.innerHTML = formattedContent;
        }
        
        messageDiv.appendChild(contentDiv);
        this.messagesContainer.appendChild(messageDiv);
        
        // Scroll to bottom smoothly
        this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;
        
        return messageId;
    }
    
    removeMessage(messageId) {
        const message = document.getElementById(messageId);
        if (message) {
            message.remove();
        }
    }
    
    formatMessage(text) {
        // Convert markdown-like formatting to HTML
        let formatted = text;
        
        // Headers (## → <h3>)
        formatted = formatted.replace(/^## (.+)$/gm, '<h3>$1</h3>');
        
        // Bold (**text** → <strong>)
        formatted = formatted.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
        
        // Lists (- item → <li>)
        formatted = formatted.replace(/^- (.+)$/gm, '<li>$1</li>');
        
        // Wrap consecutive <li> in <ul>
        formatted = formatted.replace(/(<li>.*<\/li>\n?)+/g, '<ul>$&</ul>');
        
        // Line breaks
        formatted = formatted.replace(/\n/g, '<br>');
        
        return formatted;
    }
}

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.chatApp = new ChatApp();
});