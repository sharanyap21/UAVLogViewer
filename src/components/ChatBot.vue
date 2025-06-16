<template>
    <div :class="['chatbot-container', { floating }]">
        <div class="chat-header">
        <h4>MAVLink Assistant</h4>
        <button class="close-btn" @click="close()"><i class="fa fa-times-circle" aria-hidden="true"></i></button>
        </div>
        <div class="chat-window">
        <div
            v-for="(msg, index) in messages"
            :key="index"
            class="chat-message"
            :class="msg.role"
        >
            <strong>{{ msg.role === 'user' ? 'You' : 'Bot' }}:</strong>
            <span>{{ msg.text }}</span>
        </div>
        </div>
        <form @submit.prevent="sendMessage" class="chat-input">
        <input
            v-model="newMessage"
            type="text"
            placeholder="Ask a question..."
            required
        />
        <button type="submit">Send</button>
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
                this.messages.push({ role: 'bot', text: 'This is a placeholder reply.' })
            }, 500)
        }
    },
    mounted () {
        console.log('✅ ChatBot component mounted')
        this.messages.push({ role: 'bot', text: 'Hello! How can I help you today?' })
    }
}
</script>

<style scoped>
.chatbot-container {
  position: fixed;
  bottom: 20px;
  right: 20px;
  width: 300px;
  height: 400px;
  margin: 0;
  padding: 0;
  border: 1px solid #ccc;
  border-radius: 8px;
  background: white;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
  display: flex;
  flex-direction: column;
}

.chat-header {
  padding: 0.75rem;
  background: #409eff;
  color: white;
  border-radius: 8px 8px 0 0;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.chat-header h4 {
  margin: 0;
  font-size: 1rem;
}

.close-btn {
  background: none;
  border: none;
  color: white;
  cursor: pointer;
  font-size: 1.2rem;
  padding: 0;
}

.chat-window {
  flex: 1;
  overflow-y: auto;
  padding: 1rem;
  background: #f8f8f8;
}

.chat-message {
  margin-bottom: 0.75rem;
  max-width: 80%;
}

.chat-message.user {
  text-align: right;
  color: #333;
  margin-left: auto;
}

.chat-message.bot {
  text-align: left;
  color: #2c3e50;
  margin-right: auto;
}

.chat-input {
  display: flex;
  gap: 0.5rem;
  padding: 0.75rem;
  background: white;
  border-top: 1px solid #eee;
}

.chat-input input {
  flex: 1;
  padding: 0.5rem;
  border-radius: 4px;
  border: 1px solid #ccc;
}

.chat-input button {
  padding: 0.5rem 1rem;
  border: none;
  background: #409eff;
  color: white;
  border-radius: 4px;
  cursor: pointer;
}
</style>
