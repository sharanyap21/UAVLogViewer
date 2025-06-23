import os
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*", "methods": ["GET", "POST", "OPTIONS"], "allow_headers": ["Content-Type"]}})

#========================================
# Model setup (Gemini 2.5 Flash)
#========================================
try:
    genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
    model = genai.GenerativeModel('gemini-2.5-flash')
except Exception as e:
    print(f"Error configuring Google AI, please check your API key: {e}")
    model = None

#========================================
# Column selection prompt
#========================================
def create_column_selection_prompt(user_question, telemetry_data):
    schema = ""
    for key, value in telemetry_data.items():
        if isinstance(value, dict) and value.keys():
            fields = ", ".join(value.keys())
            schema += f"- {key}: {fields}\n"

    prompt = f"""
    You are a data routing tool. Your task is to identify the single most relevant telemetry message type for answering a user's question about flight data.
    Analyze the user's question and select the best message type from the following schema.

    Schema of Available Message Types and Fields:
    {schema}

    User Question: "{user_question}"

    Based on the user's question, which message type is most likely to contain the answer?
    Return ONLY the single, exact message type name from the schema (e.g., GLOBAL_POSITION_INT, POS[0]). Do not add any explanation or extra text.
    """
    return prompt

#========================================
# Final answer prompt
#========================================
def create_final_answer_prompt(history, log_type, data_summary):
    chat_history_text = ""
    for message in history:
        role = "User" if message['role'] == 'user' else "You"
        chat_history_text += f"{role}: {message['text']}\n"

    prompt = f"""
    You are an expert UAV flight analyst. Your role is to analyze a specific slice of telemetry data from a .{log_type} log file and answer the user's question.

    Your Task:

    1. Analyze the provided targeted telemetry data summary and the user's question.
    2. Refer to the official ArduPilot log documentation when needed: https://ardupilot.org/plane/docs/logmessages.html
    3. Answer based only on the data provided. If the data is insufficient, state that clearly. For calculations like "highest" or "average", use the entire dataset implied by the summary.
    4. Behave agentically: maintain conversation context and ask for clarification if the user's query is ambiguous.
    5. For high-level questions about "anomalies," look for patterns like:
        - Sudden drops in altitude (ATT.Alt).
        - Significant battery voltage drops (BAT.Volt).
        - Loss of GPS satellites (GPS.NSats < 5).
        - Critical error messages (ERR).
        - Uncommanded flight mode changes (MODE).
    6. Targeted Telemetry Data Summary:
        {data_summary}
    7. Conversation History:
        {chat_history_text}
    8. User's new question is next. Analyze the data and history to provide a helpful, data-driven answer.
    """
    return prompt

#========================================
# Chat endpoint
#========================================
@app.route('/api/chat', methods=['POST'])
def chat_handler():
    if not model:
        return jsonify({"error": "LLM model is not configured. Check your API key."}), 500
    
    data = request.json
    user_question = data.get('question', '')
    history = data.get('history', [])
    telemetry_data = data.get('telemetryData', {})
    log_type = data.get('logType', 'log')

    if not all([user_question, telemetry_data]):
        return jsonify({"error": "Missing question or telemetry data."}), 400

    try:
        # Select the most relevant column
        column_selection_prompt = create_column_selection_prompt(user_question, telemetry_data)
        response = model.generate_content(column_selection_prompt)
        
        # Clean data
        selected_column = response.text.strip()

        # Check if the selected column is in the telemetry data
        if selected_column not in telemetry_data:
            reply = "I'm sorry, I couldn't identify the right data to answer your question. Could you please rephrase it?"
            return jsonify({"reply": reply})

        # Get data for the selected column
        relevant_data = telemetry_data.get(selected_column)
        
        # Provide data as context
        final_prompt = create_final_answer_prompt(history, log_type, relevant_data)
        
        # Generate final answer
        chat = model.start_chat(history=[])
        full_content = final_prompt + f"\nUser: {user_question}"
        final_response = chat.send_message(full_content)
        
        return jsonify({"reply": final_response.text})

    except Exception as e:
        print(f"An error occurred in the chat handler: {e}")
        return jsonify({"error": "An unexpected error occurred while processing your request."}), 500

#========================================
# Main
#========================================
if __name__ == '__main__':
    app.run(debug=True)