document.addEventListener("DOMContentLoaded", () => {
    const chatBox = document.getElementById("chat-box");
    const messageInput = document.getElementById("message-input");
    const sendButton = document.getElementById("send-button");
    const statusIndicator = document.getElementById("status-indicator");

    const addMessage = (text, sender) => {
        const messageElement = document.createElement("div");
        messageElement.classList.add("message", `${sender}-message`);
        messageElement.textContent = text;
        chatBox.appendChild(messageElement);
        chatBox.scrollTop = chatBox.scrollHeight;
        return messageElement;
    };

    const sendMessage = async () => {
        const text = messageInput.value.trim();
        if (text === "") return;

        addMessage(text, "user");
        messageInput.value = "";
        messageInput.style.height = 'auto'; // Reset height

        const thinkingMessage = addMessage("Agent is thinking...", "agent");
        thinkingMessage.classList.add("thinking");

        try {
            const response = await fetch("/chat", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({ text: text, user_id: "web_user_001" }),
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            thinkingMessage.textContent = data.text;
            thinkingMessage.classList.remove("thinking");

        } catch (error) {
            thinkingMessage.textContent = "Sorry, I couldn't connect to the agent. Please try again.";
            thinkingMessage.classList.remove("thinking");
            console.error("Error sending message:", error);
        }
    };

    const checkServerStatus = async () => {
        try {
            const response = await fetch("/status");
            if (response.ok) {
                statusIndicator.classList.add("connected");
            } else {
                statusIndicator.classList.remove("connected");
            }
        } catch (error) {
            statusIndicator.classList.remove("connected");
        }
    };

    sendButton.addEventListener("click", sendMessage);
    messageInput.addEventListener("keydown", (event) => {
        if (event.key === "Enter" && !event.shiftKey) {
            event.preventDefault();
            sendMessage();
        }
    });

    messageInput.addEventListener('input', function() {
        this.style.height = 'auto';
        this.style.height = (this.scrollHeight) + 'px';
    });

    // Check server status every 5 seconds
    setInterval(checkServerStatus, 5000);
    // Initial check
    checkServerStatus();
    addMessage("Hello! I am the Resonance Agent. How can I help you today?", "agent");
});
