document.addEventListener('DOMContentLoaded', () => {
    const chatBox = document.getElementById('chat-box');
    const messageInput = document.getElementById('message-input');
    const sendButton = document.getElementById('send-button');
    const statusIndicator = document.getElementById('status-indicator');
    const statusText = document.getElementById('status-text');

    let isProcessing = false;

    // Check backend status
    async function checkStatus() {
        try {
            const response = await fetch('/status');
            const data = await response.json();
            if (data.status === 'ok') {
                statusIndicator.classList.add('connected');
                statusIndicator.classList.remove('disconnected');
                statusText.textContent = "Neural Link: Active";
            }
        } catch (error) {
            statusIndicator.classList.remove('connected');
            statusIndicator.classList.add('disconnected');
            statusText.textContent = "Neural Link: Offline";
        }
    }

    // Load Chat History
    async function loadHistory() {
        try {
            const response = await fetch('/history');
            const data = await response.json();

            // Clear default welcome message if there is history
            if (data.history && data.history.length > 0) {
                chatBox.innerHTML = '';

                data.history.forEach(entry => {
                    if (entry.role === 'user') {
                        appendMessage('user', entry.content);
                    } else if (entry.role === 'assistant') {
                        appendMessage('assistant', entry.content, entry.thought);
                    }
                });

                scrollToBottom();
            }
        } catch (error) {
            console.error("Failed to load history:", error);
        }
    }

    // Initialize
    checkStatus();
    loadHistory();
    setInterval(checkStatus, 30000); // Check every 30s

    // Auto-resize textarea
    messageInput.addEventListener('input', function() {
        this.style.height = 'auto';
        this.style.height = (this.scrollHeight) + 'px';
        if (this.value === '') this.style.height = 'auto';
    });

    // Send Message Logic
    async function sendMessage() {
        const text = messageInput.value.trim();
        if (!text || isProcessing) return;

        isProcessing = true;
        sendButton.disabled = true;
        messageInput.value = '';
        messageInput.style.height = 'auto';

        // Add user message to UI
        appendMessage('user', text);
        scrollToBottom();

        // Show typing indicator (placeholder)
        const loadingId = appendLoadingIndicator();
        scrollToBottom();

        try {
            const response = await fetch('/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text: text })
            });

            const data = await response.json();

            // Remove loading indicator
            document.getElementById(loadingId).remove();

            // Append agent response with thought process
            appendMessage('assistant', data.text, data.thought);

        } catch (error) {
            document.getElementById(loadingId).remove();
            appendMessage('assistant', "Error: Could not connect to the neural core.");
            console.error(error);
        } finally {
            isProcessing = false;
            sendButton.disabled = false;
            scrollToBottom();
            messageInput.focus();
        }
    }

    sendButton.addEventListener('click', sendMessage);
    messageInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    // Helper: Append Message to UI
    function appendMessage(role, text, thought = null) {
        const msgDiv = document.createElement('div');
        msgDiv.className = `message ${role}`;

        const avatarIcon = role === 'user' ? '<i class="fa-solid fa-user"></i>' : '<i class="fa-solid fa-robot"></i>';

        let contentHtml = '';

        // If there's a thought process (only for assistant)
        if (thought) {
            const thoughtId = 'thought-' + Date.now();
            contentHtml += `
                <div class="thought-container">
                    <div class="thought-header" onclick="toggleThought('${thoughtId}', this)">
                        <i class="fa-solid fa-microchip"></i> Reasoning & Actions
                    </div>
                    <div id="${thoughtId}" class="thought-content">
                        ${marked.parse(thought)}
                    </div>
                </div>
            `;
        }

        // Parse Markdown for the main text
        const parsedText = marked.parse(text);

        // Add Speak Button for Assistant
        let actionButtons = '';
        if (role === 'assistant') {
            actionButtons = `
                <div class="message-actions">
                    <button class="action-btn" onclick="speakText(this)" title="Read Aloud">
                        <i class="fa-solid fa-volume-high"></i>
                    </button>
                </div>
            `;
        }

        contentHtml += `<div class="bubble">${parsedText}${actionButtons}</div>`;

        msgDiv.innerHTML = `
            <div class="avatar">${avatarIcon}</div>
            <div class="message-body">
                ${contentHtml}
            </div>
        `;

        chatBox.appendChild(msgDiv);

        // Apply syntax highlighting to new code blocks
        msgDiv.querySelectorAll('pre code').forEach((block) => {
            hljs.highlightElement(block);
        });
    }

    function appendLoadingIndicator() {
        const id = 'loading-' + Date.now();
        const div = document.createElement('div');
        div.id = id;
        div.className = 'message assistant';
        div.innerHTML = `
            <div class="avatar"><i class="fa-solid fa-robot"></i></div>
            <div class="message-body">
                <div class="bubble" style="color: #94a3b8; font-style: italic;">
                    <i class="fa-solid fa-circle-notch fa-spin"></i> Processing...
                </div>
            </div>
        `;
        chatBox.appendChild(div);
        return id;
    }

    function scrollToBottom() {
        chatBox.scrollTop = chatBox.scrollHeight;
    }

    // Global toggle function
    window.toggleThought = function(id, header) {
        const content = document.getElementById(id);
        content.classList.toggle('show');
        header.classList.toggle('active');
    }

    // TTS Function
    window.speakText = function(btn) {
        const bubble = btn.closest('.bubble');
        // Extract text only, ignoring hidden elements or buttons
        const text = bubble.innerText.replace("Reasoning & Actions", "").trim();

        if ('speechSynthesis' in window) {
            // Cancel current speech if any
            window.speechSynthesis.cancel();

            const utterance = new SpeechSynthesisUtterance(text);
            // Try to set a good voice
            const voices = window.speechSynthesis.getVoices();
            // Prefer Google US English or similar if available, or just default
            // For Azerbaijani, support might be limited, so default is safest.
            utterance.rate = 1.0;
            utterance.pitch = 1.0;

            window.speechSynthesis.speak(utterance);
        } else {
            alert("Text-to-Speech not supported in this browser.");
        }
    }
});
