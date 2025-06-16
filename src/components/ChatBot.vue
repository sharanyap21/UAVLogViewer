<template>
    <div :class="['chatbot-container', { floating }]">
        <div class="chat-header">
            <button class="close-btn" @click="close()">
                <i class="fa fa-times" aria-hidden="true"></i>
            </button>
        </div>

        <div class="chat-window">
            <div v-for="(msg, index) in messages" :key="index" class="chat-message" :class="msg.role">
                <span class="message-bubble">{{ msg.text }}</span>
            </div>
        </div>

        <form @submit.prevent="sendMessage" class="chat-input-form">
            <input v-model="newMessage" type="text" placeholder="Ask anything..." required />
            <button type="submit" class="send-btn">
                <i class="fa fa-arrow-up" aria-hidden="true"></i>
            </button>
        </form>
    </div>
</template>

<script>
export default {
    name: 'ChatBot',
    props: {
        floating: {
            type: Boolean,
            default: false
        }
    },
    data () {
        return {
            newMessage: '',
            messages: []
        }
    },
    methods: {
        close () {
            this.$emit('close')
        },
        sendMessage () {
            const userInput = this.newMessage.trim()
            if (!userInput) return

            this.messages.push({ role: 'user', text: userInput })
            this.newMessage = ''

            // Fake bot reply for demo purposes
            setTimeout(() => {
                this.messages.push({
                    role: 'bot',
                    text: 'This is a colorful placeholder reply!'
                })
            }, 500)
        }
    },
    mounted () {
        this.messages.push({ role: 'bot', text: 'What can I help with?' })
    }
}
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;700&display=swap');

.chatbot-container {
    font-family: 'Inter', sans-serif;
    position: fixed;
    bottom: 20px;
    right: 20px;
    width: 350px;
    height: 550px;
    background: #f4f6f8;
    border-radius: 24px;
    box-shadow: 0 8px 30px rgba(0, 0, 0, 0.15);
    display: flex;
    flex-direction: column;
    overflow: hidden;
    border: 1px solid #e0e0e0;
}

.chat-header {
    position: absolute;
    top: 10px;
    right: 10px;
    z-index: 10;
}

.close-btn {
    background: #dcdcdc;
    color: #555;
    border: none;
    border-radius: 50%;
    width: 28px;
    height: 28px;
    display: flex;
    justify-content: center;
    align-items: center;
    cursor: pointer;
    font-size: 0.9rem;
    transition: background-color 0.2s;
}

.close-btn:hover {
    background: #c9c9c9;
}

.chat-window {
    flex: 1;
    padding: 20px 15px;
    overflow-y: auto;
    display: flex;
    flex-direction: column;
    gap: 12px;
    margin-top: 40px;
}

.chat-window::-webkit-scrollbar {
    width: 6px;
}

.chat-window::-webkit-scrollbar-thumb {
    background: #ccc;
    border-radius: 3px;
}

.chat-window::-webkit-scrollbar-thumb:hover {
    background: #bbb;
}

.chat-message {
    display: flex;
    max-width: 85%;
}

.message-bubble {
    padding: 10px 16px;
    border-radius: 20px;
    line-height: 1.5;
    word-wrap: break-word;
}

.chat-message.bot {
    align-self: flex-start;
}

.chat-message.bot .message-bubble {
    background: #e9e9eb;
    color: #2c3e50;
    border-bottom-left-radius: 4px;
}

.chat-message.user {
    align-self: flex-end;
}

.chat-message.user .message-bubble {
    background: #2c3e50;
    color: #e9e9eb;
    border-bottom-right-radius: 4px;
}

.chat-input-form {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 15px;
    background: #ffffff;
    border-top: 1px solid #e0e0e0;
}

.chat-input-form input {
    flex: 1;
    padding: 12px 16px;
    border-radius: 20px;
    border: 1px solid #dcdcdc;
    background-color: #f4f4f4;
    font-size: 1rem;
    transition: border-color 0.2s, box-shadow 0.2s;
}

.chat-input-form input:focus {
    outline: none;
    border-color: #007aff;
    box-shadow: 0 0 0 3px rgba(0, 122, 255, 0.15);
}

.send-btn {
    width: 44px;
    height: 44px;
    border: none;
    background: #333;
    color: white;
    border-radius: 50%;
    cursor: pointer;
    display: flex;
    justify-content: center;
    align-items: center;
    font-size: 1.1rem;
    flex-shrink: 0;
    transition: background-color 0.2s;
}

.send-btn:hover {
    background: #000;
}
</style>
