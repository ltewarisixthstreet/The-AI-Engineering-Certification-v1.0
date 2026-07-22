const messagesContainer = document.getElementById('messages');
const messageInput = document.getElementById('messageInput');
const sendBtn = document.getElementById('sendBtn');

const conversationId = crypto.randomUUID();

function addMessage(text, sender) {
    const messageEl = document.createElement('div');
    messageEl.className = `message ${sender}`;

    const bubbleEl = document.createElement('div');
    bubbleEl.className = 'message-bubble';
    bubbleEl.textContent = text;

    messageEl.appendChild(bubbleEl);
    messagesContainer.appendChild(messageEl);

    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

async function sendMessage() {
    const message = messageInput.value.trim();
    if (!message) return;

    addMessage(message, 'user');
    messageInput.value = '';
    sendBtn.disabled = true;

    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message: message,
                conversation_id: conversationId,
            }),
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        addMessage(data.reply, 'assistant');
    } catch (error) {
        console.error('Error:', error);
        addMessage('Sorry, there was an error processing your message.', 'assistant');
    } finally {
        sendBtn.disabled = false;
        messageInput.focus();
    }
}

sendBtn.addEventListener('click', sendMessage);
messageInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        sendMessage();
    }
});

messageInput.focus();
