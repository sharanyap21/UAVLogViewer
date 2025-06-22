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

def get_telemetry_summary(data):
    """
    Creates a concise and accurate summary of the telemetry data from a
    columnar data structure (a dictionary of lists).
    """
    if not isinstance(data, dict) or not data:
        return "No telemetry data available."

    # For debugging: shows the structure of the data received by this function.
    # You can comment this out in production.
    # print(data)

    summary = "Available MAVLink message types:\n"
    summary += ", ".join(data.keys())
    summary += "\n\nKey Data Points (first 3 entries):\n"

    # A more accurate list of important message types to look for.
    # The function will only summarize the ones that exist in the log.
    key_messages_to_summarize = [
        'GLOBAL_POSITION_INT', 
        'ATTITUDE', 
        'HEARTBEAT', 
        'STATUSTEXT'
    ]

    for msg_type in key_messages_to_summarize:
        # Check if the message type exists in the data and is not empty
        if msg_type not in data or not data[msg_type]:
            continue

        message_object = data[msg_type]
        sample_data = []

        if not isinstance(message_object, dict):
            continue

        try:
            # Get the column/field names for this message type
            inner_keys = list(message_object.keys())
            if not inner_keys:
                continue

            # Find the number of data points (rows) from the length of the first column
            num_messages = len(message_object[inner_keys[0]])
            if num_messages == 0:
                continue

            # Reconstruct the first 3 "rows" of data from the columns
            for i in range(min(3, num_messages)):
                message_instance = {}
                for key in inner_keys:
                    # Defensively check if the column has this index
                    if i < len(message_object[key]):
                        message_instance[key] = message_object[key][i]
                    else:
                        message_instance[key] = None  # Use None if data is missing
                sample_data.append(message_instance)

            # Add the summary to the output string if we have sample data
            if sample_data:
                summary += f"- {msg_type}:\n{json.dumps(sample_data, indent=2)}\n"

        except (IndexError, KeyError, TypeError) as e:
            print(f"DEBUG: Could not process columnar data for {msg_type}: {e}")
            summary += f"- {msg_type}: [Error processing sample data]\n"
    
    return summary

def generate_prompt(telemetry_data, history, log_type):
    """
    Creates a detailed, agentic prompt for the LLM.
    """
    telemetry_summary = get_telemetry_summary(telemetry_data)
    
    # # Save telemetry_summary to a file (out_actual.txt)
    # with open('out_actual.txt', 'w') as f:
    #     f.write(telemetry_summary)
    # print("Saved telemetry_summary to out_actual.txt")

    # Tell it to fix the get_telemetry_summary function to correctly capture the output

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