# backend/app.py
import os
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

# Configure the Flask app
app = Flask(__name__)

# Apply a more permissive CORS configuration for debugging.
CORS(app, resources={r"/api/*": {
    "origins": "*",
    "methods": ["GET", "POST", "OPTIONS"],
    "allow_headers": ["Content-Type"]
}})


# Configure the Google Generative AI
try:
    genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
    model = genai.GenerativeModel('gemini-1.5-flash-latest')
except Exception as e:
    print(f"Error configuring Google AI, please check your API key: {e}")
    model = None

def generate_prompt(telemetry_data, history, log_type):
    """
    Creates a detailed, agentic prompt for the LLM.
    """
    def get_telemetry_summary(data):
        """
        Creates a concise summary of the telemetry data, correctly handling a
        columnar data structure (a dictionary of lists).
        """

        print(data)
        summary = "Available MAVLink message types:\n"
        summary += ", ".join(data.keys())
        summary += "\n\nKey Data Points (sample):\n"

        key_messages = ['GPS', 'ATT', 'BAT', 'ERR', 'STAT', 'MODE']
        for msg_type in key_messages:
            # Check if the message type exists and its data is not empty
            if msg_type in data and data[msg_type]:
                message_object = data[msg_type]
                sample_data = []  # Initialize an empty list for our samples

                # This handles the columnar data structure (dictionary of lists)
                if isinstance(message_object, dict):
                    try:
                        # Get the column names (e.g., 'TimeUS', 'Lat', 'Lng')
                        inner_keys = list(message_object.keys())
                        if not inner_keys: continue # Skip if the dictionary is empty

                        # Find the length of the first column to determine num_messages
                        num_messages = len(message_object[inner_keys[0]])

                        # Reconstruct the first 3 "rows" from the columns
                        for i in range(min(3, num_messages)):
                            message_instance = {key: message_object[key][i] for key in inner_keys}
                            sample_data.append(message_instance)

                    except (IndexError, KeyError, TypeError) as e:
                        # This handles cases where the data format is unexpected
                        print(f"DEBUG: Could not process columnar data for {msg_type}: {e}")
                        sample_data = [{"error": "Could not display sample data."}]
                
                # Fallback for the original assumption (list of dictionaries)
                elif isinstance(message_object, list):
                    sample_data = message_object[:3]

                # Add the summary line if we successfully created a sample
                if sample_data:
                    summary += f"- {msg_type}: {json.dumps(sample_data, indent=2)}\n"

        return summary

    telemetry_summary = get_telemetry_summary(telemetry_data)

    # Build conversation history for context
    chat_history_text = ""
    for message in history:
        role = "User" if message['role'] == 'user' else "You"
        chat_history_text += f"{role}: {message['text']}\n"

    # Main prompt (System Message)
    prompt = f"""
    You are an expert UAV flight analyst. Your role is to analyze telemetry data 
    from a .{log_type} log file and answer user questions.

    Your Task:

    1. Analyze the provided telemetry data summary and the user's question.
    2. Refer to the official ArduPilot log documentation when needed: https://ardupilot.org/plane/docs/logmessages.html
    3. Answer based only on the data provided. If the data is insufficient, say so.
    4. Behave agentically: maintain conversation context and ask for clarification if the user's query is ambiguous.
    5. For high-level questions about "anomalies," look for patterns like:
        - Sudden drops in altitude (ATT.Alt).
        - Significant battery voltage drops (BAT.Volt).
        - Loss of GPS satellites (GPS.NSats < 5).
        - Critical error messages (ERR).
        - Uncommanded flight mode changes (MODE).
    6. Telemetry Data Summary:
        {telemetry_summary}
    7. Conversation History:
        {chat_history_text}
    8. User's new question is next. Analyze the data and history to provide a helpful, data-driven answer.
    """

    return prompt
@app.route('/api/chat', methods=['POST'])
def chat_handler():
    if not model:
        return jsonify({"error": "LLM model is not configured. Check your API key."}), 500
    
    data = request.json
    telemetry_data = data.get('telemetryData', {})
    history = data.get('history', [])
    user_question = data.get('question', '')
    log_type = data.get('logType', 'log') # Extract logType

    if not user_question:
        return jsonify({"error": "No question provided"}), 400
    if not telemetry_data:
        # This check is now more of a fallback, as the UI prevents this.
        return jsonify({"reply": "I can't answer questions without telemetry data. Please upload a log file first."})

    # Generate the full prompt including persona, data, history, and log type
    prompt = generate_prompt(telemetry_data, history, log_type)
    
    # Create a chat session with history
    chat = model.start_chat(history=[]) # We are manually formatting history in the prompt for more control

    try:
        # The final content sent to the model is the prompt + the new question
        full_content = prompt + f"User: {user_question}"
        response = chat.send_message(full_content)
        return jsonify({"reply": response.text})
    except Exception as e:
        print(f"An error occurred: {e}")
        return jsonify({"error": "Failed to get a response from the AI model."}), 500

if __name__ == '__main__':
    app.run(debug=True)