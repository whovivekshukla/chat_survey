import streamlit as st
from openai import OpenAI
import json
import time

# Initialize OpenAI client
client = OpenAI()

SURVEY_JSON = {
    "Survey": {
        "Title": "CAHPS Health Plan Survey Adult Medicaid Survey 5.1",
        "Version": "5.1",
        "Language": "English",
        "Questions": [
            {
                "QuestionID": 1,
                "QuestionText": "Did you have an illness, injury, or condition that needed care right away?",
                "Options": ["Yes", "No"],
                "SkipLogic": {"Yes": "Q2", "No": "Q3"}
            },
            {
                "QuestionID": 2,
                "QuestionText": "When you needed care right away, how often did you get care as soon as you needed?",
                "Options": ["Never", "Sometimes", "Usually", "Always"]
            },
            {
                "QuestionID": 3,
                "QuestionText": "Did you make appointments for check-up or routine care?",
                "Options": ["Yes", "No"],
                "SkipLogic": {"Yes": "Q4", "No": "Q5"}
            },
            {
                "QuestionID": 4,
                "QuestionText": "How often did you get an appointment as soon as you needed?",
                "Options": ["Never", "Sometimes", "Usually", "Always"]
            },
            {
                "QuestionID": 5,
                "QuestionText": "How many times did you get healthcare in person, phone, or video?",
                "Options": ["None", "1 time", "2", "3", "4", "5 to 9", "10 or more"],
                "SkipLogic": {"None": "Q8"}
            },
            {
                "QuestionID": 6,
                "QuestionText": "Rate your healthcare on a scale from 0 to 10.",
                "Scale": {"Min": 0, "Max": 10}
            },
            {
                "QuestionID": 7,
                "QuestionText": "How often was it easy to get care, tests, or treatment you needed?",
                "Options": ["Never", "Sometimes", "Usually", "Always"]
            },
            {
                "QuestionID": 8,
                "QuestionText": "Do you have a personal doctor?",
                "Options": ["Yes", "No"],
                "SkipLogic": {"Yes": "Q9", "No": "Q15"}
            },
            {
                "QuestionID": 9,
                "QuestionText": "How many times did you meet with your personal doctor?",
                "Options": ["None", "1 time", "2", "3", "4", "5 to 9", "10 or more"],
                "SkipLogic": {"None": "Q14"}
            },
            {
                "QuestionID": 10,
                "QuestionText": "How often did your personal doctor explain things clearly?",
                "Options": ["Never", "Sometimes", "Usually", "Always"]
            },
            {
                "QuestionID": 11,
                "QuestionText": "How often did your personal doctor listen carefully to you?",
                "Options": ["Never", "Sometimes", "Usually", "Always"]
            },
            {
                "QuestionID": 12,
                "QuestionText": "How often did your personal doctor show respect?",
                "Options": ["Never", "Sometimes", "Usually", "Always"]
            },
            {
                "QuestionID": 13,
                "QuestionText": "How often did your personal doctor spend enough time with you?",
                "Options": ["Never", "Sometimes", "Usually", "Always"]
            },
            {
                "QuestionID": 14,
                "QuestionText": "Rate your personal doctor on a scale from 0 to 10.",
                "Scale": {"Min": 0, "Max": 10}
            },
            {
                "QuestionID": 15,
                "QuestionText": "Did you see a specialist?",
                "Options": ["Yes", "No"],
                "SkipLogic": {"Yes": "Q16", "No": "Q19"}
            },
            {
                "QuestionID": 16,
                "QuestionText": "How often did you get an appointment with a specialist as soon as needed?",
                "Options": ["Never", "Sometimes", "Usually", "Always"]
            },
            {
                "QuestionID": 17,
                "QuestionText": "How many specialists did you see?",
                "Options": ["None", "1", "2", "3", "4", "5 or more"]
            },
            {
                "QuestionID": 18,
                "QuestionText": "Rate the specialist you saw most often.",
                "Scale": {"Min": 0, "Max": 10}
            },
            {
                "QuestionID": 19,
                "QuestionText": "Did you contact customer service?",
                "Options": ["Yes", "No"],
                "SkipLogic": {"Yes": "Q20", "No": "Q22"}
            },
            {
                "QuestionID": 20,
                "QuestionText": "How often did customer service help you as needed?",
                "Options": ["Never", "Sometimes", "Usually", "Always"]
            },
            {
                "QuestionID": 21,
                "QuestionText": "How often did customer service treat you with courtesy?",
                "Options": ["Never", "Sometimes", "Usually", "Always"]
            },
            {
                "QuestionID": 22,
                "QuestionText": "Did you receive any forms from your health plan?",
                "Options": ["Yes", "No"],
                "SkipLogic": {"No": "Q24"}
            },
            {
                "QuestionID": 23,
                "QuestionText": "How often were the forms easy to fill out?",
                "Options": ["Never", "Sometimes", "Usually", "Always"]
            },
            {
                "QuestionID": 24,
                "QuestionText": "Rate your health plan on a scale from 0 to 10.",
                "Scale": {"Min": 0, "Max": 10}
            }
        ]
    }
}

# Supported languages
SUPPORTED_LANGUAGES = {
    "english": {"code": "en", "name": "English"},
    "spanish": {"code": "es", "name": "Spanish"},
    "español": {"code": "es", "name": "Spanish"},
    "hindi": {"code": "hi", "name": "Hindi"},
    "हिंदी": {"code": "hi", "name": "Hindi"},
    "chinese": {"code": "zh", "name": "Chinese"},
    "中文": {"code": "zh", "name": "Chinese"},
    "french": {"code": "fr", "name": "French"},
    "français": {"code": "fr", "name": "French"}
}

def initialize_session_state():
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    if 'current_question' not in st.session_state:
        st.session_state.current_question = 1
    if 'responses' not in st.session_state:
        st.session_state.responses = {}
    if 'survey_started' not in st.session_state:
        st.session_state.survey_started = False
    if 'survey_completed' not in st.session_state:
        st.session_state.survey_completed = False
    if 'language' not in st.session_state:
        st.session_state.language = None
    if 'language_selected' not in st.session_state:
        st.session_state.language_selected = False
    if 'responses_saved' not in st.session_state:
        st.session_state.responses_saved = False

def get_question_by_id(question_id):
    for question in SURVEY_JSON["Survey"]["Questions"]:
        if question["QuestionID"] == question_id:
            return question
    return None

def validate_response(question, response):
    system_prompt = f"""
    You are an AI assistant helping to validate survey responses. 
    Your task is to determine if a given response is valid for the question asked.
    Consider ranges in options, such as "5 to 9", and validate if the response falls within any specified range.
    Respond with only 'true' if the response is valid, or 'false' if it's invalid.
    
    IMPORTANT: The user is responding in {st.session_state.language['name']}. Consider responses valid if they match the meaning in any language.
    """

    valid_options = question.get('Options', question.get('Scale', 'Any response'))
    print(f"Valid options: {valid_options}")
    print(f"User response: {response}")
    
    user_prompt = f"""
    Question: {question['QuestionText']}
    Valid options: {valid_options}
    User response: {response}
    """

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]

    try:
        ai_response = client.chat.completions.create(
            model="gpt-4",
            messages=messages,
            temperature=0
        )
        return ai_response.choices[0].message.content.lower() == 'true'
    except Exception as e:
        st.error(f"Error validating response: {e}")
        return False
    
def interpret_response(question, response):
    system_prompt = f"""
    You are an AI assistant helping to interpret survey responses. 
    Your task is to map the given response to the closest valid option for the question.
    Respond with only the mapped option, or 'INVALID' if no mapping is possible.
    
    IMPORTANT: The user is responding in {st.session_state.language['name']}. Map their response to the English option that matches the meaning.
    """

    user_prompt = f"""
    Question: {question['QuestionText']}
    Valid options: {question.get('Options', question.get('Scale', 'Any response'))}
    User response: {response}

    What is the interpreted response?
    """

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]

    try:
        ai_response = client.chat.completions.create(
            model="gpt-4",
            messages=messages,
            temperature=0
        )
        return ai_response.choices[0].message.content
    except Exception as e:
        st.error(f"Error interpreting response: {e}")
        return "INVALID"

def generate_ai_message(question, is_invalid=False, off_topic=False):
    system_prompt = f"""
    You are a healthcare survey assistant. Your goal is to:
    1. Ask survey questions directly and clearly
    2. Keep users focused on the survey
    3. Validate their responses
    4. Give brief acknowledgments
    5. If they go off-topic, redirect them to the survey
    
    Important guidelines:
    - Don't start with phrases like "I hope you're keeping well" or "I'd be happy to help"
    - Don't add unnecessary pleasantries
    - Go straight to the question
    - Keep responses concise
    - Maintain a professional tone
    - Don't add "I'm just curious" or similar phrases
    
    IMPORTANT: Respond ONLY in {st.session_state.language['name']} language.
    """

    if off_topic:
        prompt = f"""The user has gone off-topic. Politely acknowledge their comment and redirect them back to the current survey question:
        Current question: {question['QuestionText']}
        Options: {question.get('Options', question.get('Scale', ''))}
        """
    elif is_invalid:
        prompt = f"""The user provided an invalid response. Politely explain the valid options and ask the question again:
        Question: {question['QuestionText']}
        Valid options: {question.get('Options', question.get('Scale', ''))}
        """
    else:
        prompt = f"""Ask this survey question in a conversational way:
        Question: {question['QuestionText']}
        Options: {question.get('Options', question.get('Scale', ''))}
        """

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt}
    ]

    response = client.chat.completions.create(
        model="gpt-4",
        messages=messages,
        temperature=0.7
    )

    return response.choices[0].message.content

def is_off_topic(user_input, current_question):
    system_prompt = """
    You are a survey assistant. Determine if the user's response is relevant to the current question.
    Return only "true" if the response is off-topic or "false" if it's a valid attempt to answer the question.
    """

    prompt = f"""
    Current question: {current_question['QuestionText']}
    Valid options: {current_question.get('Options', current_question.get('Scale', ''))}
    User response: {user_input}
    """

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt}
    ]

    response = client.chat.completions.create(
        model="gpt-4",
        messages=messages,
        temperature=0
    )

    return response.choices[0].message.content.lower() == "true"

def get_next_question_id(current_question_id, user_response):
    current_question = get_question_by_id(current_question_id)
    interpreted_response = interpret_response(current_question, user_response)
    
    if "SkipLogic" in current_question:
        next_question_id = current_question["SkipLogic"].get(interpreted_response)
        if next_question_id:
            return int(next_question_id[1:])  # Remove 'Q' prefix and convert to int
    
    questions = SURVEY_JSON["Survey"]["Questions"]
    current_index = next((i for i, q in enumerate(questions) if q["QuestionID"] == current_question_id), -1)
    if current_index < len(questions) - 1:
        return questions[current_index + 1]["QuestionID"]
    return None

def save_survey_responses():
    """Simulate saving survey responses and return success message"""
    try:
        # Here you would typically save to a database or file
        # For now, we'll just simulate a save
        time.sleep(1)  # Simulate save operation
        st.session_state.responses_saved = True
        return True
    except Exception as e:
        st.error(f"Error saving responses: {str(e)}")
        return False

def main():
    st.title("Healthcare Survey Assistant")
    st.markdown(
        r"""
        <style>
        .stAppDeployButton {
                visibility: hidden;
            }
        </style>
        """, unsafe_allow_html=True
    )
    initialize_session_state()

    # Handle language selection first
    if not st.session_state.language_selected:
        if len(st.session_state.messages) == 0:
            language_prompt = """Please select your preferred language / Por favor, seleccione su idioma preferido / कृपया अपनी पसंदीदा भाषा चुनें / 请选择您的首选语言 / Veuillez sélectionner votre langue préférée:

Available languages:
- English
- Spanish (Español)
- Hindi (हिंदी)
- Chinese (中文)
- French (Français)

Type your preferred language:"""
            st.session_state.messages.append({
                "role": "assistant",
                "content": language_prompt
            })

    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])

    # Handle user input
    if user_input := st.chat_input("Your response"):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": user_input})

        # Handle language selection
        if not st.session_state.language_selected:
            user_language = user_input.lower().strip()
            if user_language in SUPPORTED_LANGUAGES:
                st.session_state.language = SUPPORTED_LANGUAGES[user_language]
                st.session_state.language_selected = True
                welcome_question = {
                    "QuestionText": "Hi there! At Health New England, your feedback is important to us. Would you be willing to take a brief survey about your recent healthcare experiences? Your input helps us improve the care and services we offer.",
                    "Options": ["Yes", "No"]
                }
                welcome_message = generate_ai_message(welcome_question)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": welcome_message
                })
            else:
                error_message = """Invalid language selection. Please type one of the following:
- English
- Spanish/Español
- Hindi/हिंदी
- Chinese/中文
- French/Français"""
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": error_message
                })
        
        # Handle survey after language is selected
        else:
            # Handle initial survey start
            if len(st.session_state.messages) <= 3 and user_input.lower() in ['yes', 'sí', 'हाँ', '是', 'oui']:
                initial_question = generate_ai_message(get_question_by_id(1))
                st.session_state.messages.append({"role": "assistant", "content": initial_question})
                st.session_state.current_question = 1
                st.session_state.survey_started = True
            
            # Handle ongoing survey
            elif not st.session_state.survey_completed:
                current_question = get_question_by_id(st.session_state.current_question)
                is_valid = validate_response(current_question, user_input)
                
                if is_valid:
                    interpreted_response = interpret_response(current_question, user_input)
                    st.session_state.responses[current_question["QuestionID"]] = interpreted_response
                    
                    next_question_id = get_next_question_id(st.session_state.current_question, user_input)
                    next_question = get_question_by_id(next_question_id)
                    
                    if next_question:
                        st.session_state.current_question = next_question_id
                        response = generate_ai_message(next_question)
                        st.session_state.messages.append({"role": "assistant", "content": response})
                    else:
                        # Save survey responses
                        if save_survey_responses():
                            # Survey complete with save confirmation
                            thank_you_message = "Thank you! Your survey responses have been successfully saved. We appreciate your participation in our healthcare survey."
                            st.session_state.messages.append({"role": "assistant", "content": thank_you_message})
                            st.session_state.survey_completed = True
                        else:
                            error_message = {
                                "QuestionText": "We encountered an error saving your responses. Please try again.",
                                "Options": []
                            }
                            error_response = generate_ai_message(error_message)
                            st.session_state.messages.append({"role": "assistant", "content": error_response})
                else:
                    response = generate_ai_message(current_question, is_invalid=True)
                    st.session_state.messages.append({"role": "assistant", "content": response})

        st.rerun()

if __name__ == "__main__":
    main()