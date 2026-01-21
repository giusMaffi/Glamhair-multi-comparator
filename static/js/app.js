// Glamhair AI Assistant - Frontend
// MVP Version

class ChatApp {
    constructor() {
        this.sessionId = null;
        this.baseUrl = window.location.origin;
        
        // DOM elements
        this.messagesContainer = document.getElementById('chat-messages');
        this.userInput = document.getElementById('user-input');
        this.sendButton = document.getElementById('send-button');
        this.statusIndicator = document.getElementById('status-indicator');
        this.statusText = document.getElementById('status-text');
        this.sessionIdDisplay = document.getElementById('session-id');
        
        this.init();
    }
    
    async init() {
        // Setup event listeners
        this.sendButton.addEventListener('click', () => this.sendMessage());
        this.userInput.addEventListener('keydown', (e) => {
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
        
        // Start session
        await this.startSession();
    }
    
    async startSession() {
        try {
            this.updateStatus('connecting', 'Connecting...');
            
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
            this.sessionIdDisplay.textContent = this.sessionId.substring(0, 8) + '...';
            
            this.updateStatus('connected', 'Connected');
            console.log('Session started:', this.sessionId);
            
        } catch (error) {
            console.error('Error starting session:', error);
            this.updateStatus('error', 'Connection failed');
            this.addMessage('assistant', '❌ Errore di connessione. Ricarica la pagina.');
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
        
        // Disable input
        this.userInput.disabled = true;
        this.sendButton.disabled = true;
        
        // Add user message
        this.addMessage('user', message);
        this.userInput.value = '';
        this.userInput.style.height = 'auto';
        
        // Show loading
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
        const messageId = 'msg-' + Date.now();
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${role}`;
        messageDiv.id = messageId;
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        contentDiv.textContent = content;
        
        messageDiv.appendChild(contentDiv);
        this.messagesContainer.appendChild(messageDiv);
        
        // Scroll to bottom
        this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;
        
        return messageId;
    }
    
    removeMessage(messageId) {
        const message = document.getElementById(messageId);
        if (message) {
            message.remove();
        }
    }
}

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.chatApp = new ChatApp();
});
