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
    You are an expert data routing tool for flight telemetry logs. Your task is to identify the **absolute minimum** set of telemetry message types required to answer a user's question.

    Instructions:
    1. Analyze the user's question and the provided schema.
    2. Select the single most relevant message type if possible.
    3. Only select multiple message types if it is **strictly necessary** to correlate information to answer the question (e.g., questions about "anomalies" which require checking BAT, GPS, ERR, and MODE).
    4. Be as conservative as possible. Do not include extra message types "just in case."
    5. Unless the user's question is about the attitude of the vehicle, do not select ATT.

    Schema of Available Message Types and Fields:
    {schema}

    User Question: "{user_question}"

    Return a comma-separated list of the exact message type name(s) from the schema (e.g., GLOBAL_POSITION_INT or ATT,BAT,GPS,ERR,MODE). Do not add any explanation or extra text.
    """
    return prompt

#========================================
# Iterative analysis prompt
#========================================
def create_iterative_analysis_prompt(user_question, column_name, column_data_summary):
    prompt = f"""
    You are a data analysis sub-agent. Your task is to analyze a single column of telemetry data and report findings related to the user's question.

    **User's overarching question:** "{user_question}"

    **Data to analyze (from log column '{column_name}'):**
    {column_data_summary}

    **Your Instructions:**
    - Analyze ONLY the data provided above.
    - Summarize any relevant patterns, values, or anomalies found in THIS data that might help answer the user's main question.
    - Be concise.
    - **Do not attempt to provide a final answer to the user.** Your output will be combined with other analyses.
    - Output your findings as a short, analytical summary.
    """
    return prompt

#========================================
# Synthesis prompt
#========================================
def create_synthesis_prompt(user_question, history, partial_analyses):
    chat_history_text = ""
    for message in history:
        role = "User" if message['role'] == 'user' else "You"
        chat_history_text += f"{role}: {message['text']}\n"

    analysis_text = "\n".join(f"- Analysis of {analysis['column']}: {analysis['summary']}" for analysis in partial_analyses)

    prompt = f"""
    You are an expert UAV flight analyst. Your role is to synthesize preliminary findings from various data logs into a final, comprehensive answer for the user.

    **Conversation History:**
    {chat_history_text}

    **User's Current Question:**
    "{user_question}"

    **Preliminary Data Analyses:**
    {analysis_text}

    **Your Task:**
    1. Review the user's question and the preliminary analyses.
    2. Synthesize all the information into a single, cohesive, and easy-to-understand answer.
    3. Do not mention that you reviewed "preliminary analyses" or talk about your internal process. Act as a single, authoritative expert.
    4. If the combined analyses are insufficient to answer the question, state that clearly.
    5. Answer based *only* on the provided analyses and history. Refer to the official ArduPilot log documentation when needed: https://ardupilot.org/plane/docs/logmessages.html
    """
    return prompt

#========================================
# Chat endpoint
#========================================
@app.route('/api/chat', methods=['POST'])
def chat_handler():
    if not model:
        return jsonify({"error": "LLM model is not configured. Check your API key."}), 500
    
    # Get data from request
    data = request.json
    user_question = data.get('question', '')
    history = data.get('history', [])
    telemetry_data = data.get('telemetryData', {})

    if not all([user_question, telemetry_data]):
        return jsonify({"error": "Missing question or telemetry data."}), 400

    try:
        # 1. Select the most relevant columns
        column_selection_prompt = create_column_selection_prompt(user_question, telemetry_data)
        response = model.generate_content(column_selection_prompt)
        selected_columns_str = response.text.strip()
        selected_columns = [col.strip() for col in selected_columns_str.split(',') if col.strip()]

        # 2. Check if the selected columns are in the telemetry data
        valid_selected_columns = [col for col in selected_columns if col in telemetry_data]
        if not valid_selected_columns:
            reply = "I'm sorry, I couldn't identify the right data to answer your question. Could you please rephrase it?"
            return jsonify({"reply": reply})

        # 3. Analyze the selected columns
        partial_analyses = []
        for column_name in valid_selected_columns:
            column_data = telemetry_data.get(column_name)
            if not column_data:
                continue

            column_data_summary = json.dumps({column_name: column_data}, indent=2)
            iterative_prompt = create_iterative_analysis_prompt(user_question, column_name, column_data_summary)
            iterative_response = model.generate_content(iterative_prompt)
            partial_analyses.append({
                "column": column_name,
                "summary": iterative_response.text
            })

        if not partial_analyses:
            return jsonify({"error": "Failed to analyze the relevant data columns."}), 500

        # 4. Synthesize the results
        synthesis_prompt = create_synthesis_prompt(user_question, history, partial_analyses)
        final_response = model.generate_content(synthesis_prompt)
        
        return jsonify({"reply": final_response.text})

    except Exception as e:
        print(f"An error occurred in the chat handler: {e}")
        return jsonify({"error": "An unexpected error occurred while processing your request."}), 500

#========================================
# Main
#========================================
if __name__ == '__main__':
    app.run(debug=True)