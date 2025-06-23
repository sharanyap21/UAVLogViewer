# backend/app.py

import os
import json
import re
from flask import Flask, request, jsonify
from flask_cors import CORS
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*", "methods": ["GET", "POST", "OPTIONS"], "allow_headers": ["Content-Type"]}})

try:
    genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
    model = genai.GenerativeModel('gemini-2.5-flash')
except Exception as e:
    print(f"Error configuring Google AI, please check your API key: {e}")
    model = None

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
    if not isinstance(column_data, dict) or not column_data:
        return f"No data available for message type {column_name}."

    summary = f"Data Summary for message type '{column_name}':\n"
    sample_data = []
    
    try:
        all_fields = list(column_data.keys())
        print(f"DEBUG: All fields: {all_fields}")
        if not all_fields: return summary + "[No fields found]"

        field_priority = ['TimeUS', 'time_boot_ms', 'Alt', 'relative_alt', 'Roll', 'Pitch', 'Yaw', 'Vbat', 'Curr', 'Mode', 'Text']
        fields_to_summarize = [f for f in field_priority if f in all_fields]
        print(f"DEBUG: Fields to summarize: {fields_to_summarize}")
        if not fields_to_summarize:
            fields_to_summarize = all_fields[:5]

        num_messages = len(column_data[all_fields[0]])
        print(f"DEBUG: Number of messages: {num_messages}")
        if num_messages == 0: return summary + "[Message type is empty]"
        
        for i in range(min(5, num_messages)):
            message_instance = {}
            for key in fields_to_summarize:
                if i < len(column_data[key]):
                    value = column_data[key][i]
                    if isinstance(value, list):
                        message_instance[key] = value[0] 
                    else:
                        message_instance[key] = value
            sample_data.append(message_instance)
            
        if sample_data:
            summary += f"Fields: {', '.join(fields_to_summarize)}\n"
            summary += json.dumps(sample_data, indent=2)

    except Exception as e:
        print(f"DEBUG: Error processing data for {column_name}: {e}")
        summary += f"[Error processing sample data for {column_name}]"
    
    return summary

def create_final_answer_prompt(user_question, history, log_type, data_summary):
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
        # --- STEP 1: IDENTIFY THE RELEVANT COLUMN ---
        column_selection_prompt = create_column_selection_prompt(user_question, telemetry_data)
        response = model.generate_content(column_selection_prompt)
        
        # Clean the response to get a valid key that might have an instance number
        selected_column = response.text.strip()
        print(f"--- LLM selected column: '{selected_column}' ---")

        if selected_column not in telemetry_data:
            print(f"Error: LLM returned an invalid column name: '{selected_column}'. Falling back.")
            reply = "I'm sorry, I couldn't identify the right data to answer your question. Could you please rephrase it?"
            return jsonify({"reply": reply})

        # --- STEP 2: RETRIEVE AND SUMMARIZE DATA FOR THE SELECTED COLUMN ---
        relevant_data = telemetry_data.get(selected_column)
        
        # --- STEP 3: GENERATE THE FINAL ANSWER USING THE TARGETED DATA ---
        final_prompt = create_final_answer_prompt(user_question, history, log_type, relevant_data)
        
        chat = model.start_chat(history=[])
        full_content = final_prompt + f"\nUser: {user_question}"
        final_response = chat.send_message(full_content)
        
        print(f"--- LLM Final Reply: '{final_response.text}' ---\n")
        return jsonify({"reply": final_response.text})

    except Exception as e:
        print(f"An error occurred in the chat handler: {e}")
        return jsonify({"error": "An unexpected error occurred while processing your request."}), 500

if __name__ == '__main__':
    app.run(debug=True)