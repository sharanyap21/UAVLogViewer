<template>
    <div :class="['chatbot-container', { floating }]">
        <!-- Close button is always visible -->
        <div class="chat-header">
            <button class="close-btn" @click="close()">
                <i class="fa fa-times" aria-hidden="true"></i>
            </button>
        </div>

        <!-- Chat View: Always shown, as the component only renders after a file is loaded -->
        <div class="chat-view">
            <div class="chat-window" ref="chatWindow">
                <div v-for="(msg, index) in messages" :key="index" class="chat-message" :class="msg.role">
                    <span class="message-bubble" v-html="formatMessage(msg.text)"></span>
                </div>
                <div v-if="isLoading" class="chat-message bot">
                    <span class="message-bubble loading-bubble">
                        <span></span><span></span><span></span>
                    </span>
                </div>
            </div>

            <form @submit.prevent="sendMessage" class="chat-input-form">
                <input v-model="newMessage" type="text" placeholder="Ask anything..." :disabled="isLoading" required />
                <button type="submit" class="send-btn" :disabled="isLoading">
                    <i class="fa fa-arrow-up" aria-hidden="true"></i>
                </button>
            </form>
        </div>
    </div>
</template>

<script>
import axios from 'axios'
import { store } from '@/components/Globals.js' // Import global state

export default {
    name: 'ChatBot',
    props: {
        floating: {
            type: Boolean,
            default: false
        },
        logType: {
            type: String,
            required: true
        }
    },
    data () {
        return {
            state: store, // Make global state available locally
            newMessage: '',
            messages: [],
            isLoading: false
        }
    },
    methods: {
        close () {
            this.$emit('close')
        },
        async sendMessage () {
            const userInput = this.newMessage.trim()
            if (!userInput || this.isLoading) return

            this.messages.push({ role: 'user', text: userInput })
            this.newMessage = ''
            this.scrollToBottom()
            this.isLoading = true

            // The payload now uses the global telemetry data and the passed-in logType
            const payload = {
                question: userInput,
                history: this.messages.slice(0, -1),
                telemetryData: this.state.messages,
                logType: this.logType
            }

            try {
                const response = await axios.post('http://127.0.0.1:5000/api/chat', payload)
                this.messages.push({ role: 'bot', text: response.data.reply })
            } catch (error) {
                console.error('Error contacting chatbot backend:', error)
                this.messages.push({ role: 'bot', text: "Sorry, I'm having trouble connecting." })
            } finally {
                this.isLoading = false
                this.scrollToBottom()
            }
        },
        scrollToBottom () {
            this.$nextTick(() => {
                const chatWindow = this.$refs.chatWindow
                if (chatWindow) chatWindow.scrollTop = chatWindow.scrollHeight
            })
        },
        formatMessage (text) {
            if (typeof text !== 'string') return ''
            return text.replace(/\n/g, '<br>')
        }
    },
    mounted () {
        // Since the chatbot is only visible after a file is loaded,
        // we can greet the user immediately.
        if (this.messages.length === 0) {
            this.messages.push({
                role: 'bot',
                text: `Log file <b>${this.state.file}</b> is loaded. What would you like to know?`
            })
        }
    },
    watch: {
        messages () {
            this.scrollToBottom()
        }
    }
}
</script>

<!-- Styles are unchanged -->
<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;700&display=swap');

/* Main container styles */
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
    z-index: 20;
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

/* --- Uploader Styles --- */
.uploader-view {
    flex: 1;
    display: flex;
    justify-content: center;
    align-items: center;
    padding: 20px;
}

.drop-area {
    position: relative;
    width: 100%;
    height: 100%;
    border: 2px dashed #b0b0b0;
    border-radius: 20px;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    text-align: center;
    color: #555;
    transition: background-color 0.2s, border-color 0.2s;
}

.drop-area.drag-over {
    background-color: #eaf2ff;
    border-color: #007aff;
}

.upload-icon {
    font-size: 48px;
    color: #007aff;
    margin-bottom: 16px;
}

.upload-title {
    font-size: 1.2rem;
    font-weight: 500;
    margin: 0 0 4px 0;
}

.upload-subtitle {
    font-size: 0.9rem;
    color: #777;
    margin: 0;
}

.upload-or {
    margin: 16px 0;
    font-size: 0.9rem;
    color: #999;
}

.upload-btn {
    background-color: #007aff;
    color: white;
    border: none;
    border-radius: 10px;
    padding: 10px 20px;
    font-size: 1rem;
    font-weight: 500;
    cursor: pointer;
    transition: background-color 0.2s;
}

.upload-btn:hover {
    background-color: #0056b3;
}
.processing-overlay {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(255, 255, 255, 0.8);
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    border-radius: 20px;
}

.spinner {
  border: 4px solid rgba(0, 0, 0, 0.1);
  width: 36px;
  height: 36px;
  border-radius: 50%;
  border-left-color: #007aff;
  animation: spin 1s ease infinite;
  margin-bottom: 10px;
}
@keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }

/* Chat View and Message Styles */
.chat-view {
    flex: 1;
    display: flex;
    flex-direction: column;
    overflow: hidden;
    padding-top: 40px;
}

.chat-window {
    flex: 1;
    padding: 0 15px 20px 15px;
    overflow-y: auto;
    display: flex;
    flex-direction: column;
    gap: 12px;
}

.chat-window::-webkit-scrollbar {
    width: 6px;
}

.chat-window::-webkit-scrollbar-thumb {
    background: #ccc;
    border-radius: 3px;
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

.chat-message.bot { align-self: flex-start; }
.chat-message.bot .message-bubble { background: #e9e9eb; color: #0d1217; border-bottom-left-radius: 4px; }
.chat-message.user { align-self: flex-end; }
.chat-message.user .message-bubble { background: #2c3e50; color: #e9e9eb; border-bottom-right-radius: 4px; }

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
    font-size: 1rem;
}

.chat-input-form input:focus {
    outline: none;
    border-color:
    #007aff;
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
}

.send-btn:hover {
    background: #000;
}

.chat-input-form input:disabled,

.chat-input-form button:disabled {
    opacity: 0.5;
    cursor: not-allowed;
}

/* Loading Bubble for bot typing */
.loading-bubble {
    display: flex;
    align-items: center;
    gap: 5px;
    padding: 14px 16px;
}

.loading-bubble span {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background-color: #999;
    animation: bounce 1.4s infinite ease-in-out both;
}

.loading-bubble span:nth-child(1) {
    animation-delay: -0.32s;
}

.loading-bubble span:nth-child(2) {
    animation-delay: -0.16s;
}

@keyframes bounce { 0%, 80%, 100% { transform: scale(0); } 40% { transform: scale(1.0); } }
</style>
