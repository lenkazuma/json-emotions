#OpenAI/FC/Wiki

import streamlit as st
from openai import OpenAI
from langchain_community.chat_models import ChatOpenAI
from langchain.chains import RetrievalQA
import time
import sys

import asyncio
import json

# Ensure an event loop is available and set it as the current event loop
loop = asyncio.get_event_loop_policy().new_event_loop()
asyncio.set_event_loop(loop)



llm = ChatOpenAI(
    model_name="gpt-4o",
    streaming=True
)

action_list = ["wave","node","rotate","jump","blink"]


# Simplify button clicks handling
def handle_button_click(question_key):
    st.session_state.clicked_question = question_key

def stream_data(answer):
    for word in answer.split():
        yield word + " "
        time.sleep(0.05)

#general ask without using vectorstore,no rag
# def ask_general(question):
#     client=OpenAI()

#     response = client.chat.completions.create(
#         model="gpt-4o",  # Adjust to the latest available GPT-4 model
#         temperature= 0.1,
#         messages=[
#             {"role": "system", "content": "You are a helpful assistant that kindly answers the question to any topic."},
#             {"role": "user", "content": question}
#         ]
#     )
#     return response.choices[0].message.content

# Process and display the question and answer
def process_question(question):
    # Add user message to chat history
    with st.chat_message("user"):
            st.markdown(question)

    with st.chat_message("assistant"):
        #st.markdown(answer)
        prompt = f'''
        Find if the following instruction contains any action order in list {action_list}. Only answer in english.
        Intruction: {question}.
        '''
        messages = [{"role": "user", "content": prompt}]
        response_message = fc_call(messages)  # Pass as list if not already handled
        img = None  # Default result to None to handle exceptions

        try:
            # Which function call was invoked
            function_called = response_message.function_call.name
            # Extracting the arguments
            function_args  = json.loads(response_message.function_call.arguments)
            # Function names
            available_functions = {'get_action': get_action}
            function_to_call = available_functions[function_called]
            action = function_to_call(*list(function_args.values()))
            st.write(action)

        except Exception as e:
            print(f"No Function called, error: {e}")
        
        user_feedback=None
        col1,col2,col3,col4 = st.columns([3,3,0.5,0.5])
        with col3:
                if st.button(":thumbsup:"):
                    print("Like")
                    user_feedback = 1
        with col4:
                if st.button(":thumbsdown:"):
                    print("Dislike")
                    user_feedback = 0
    # Add assistant response to chat history
    st.session_state.history.append({"role": "assistant","score":user_feedback,"action":action})
# Reset clicked_question to prevent it from affecting subsequent actions
st.session_state.clicked_question = None

## ======================================
## Function call related
## ======================================
def fc_call(messages):
    # Ensure messages is a list
    client=OpenAI()
    if not isinstance(messages, list):
        messages = [messages]
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        temperature=0.1,
        functions=[
            {
                "name": "get_action",
                "description": "Get the action in the text.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "action_name": {
                            "type": "string",
                            "description": "The action. In less 1 word, only in english"
                        }
                    },
                    "required": ["action"]
                },
                 "responses": {
                    "type": "object",
                    "properties": {
                        "image_data": {
                            "type": "string",
                            "description": "The main action file to run, only 1 word."
                        }
                    }
                }
            }
        ],
        function_call = 'auto'
    )
    return response.choices[0].message



def get_action(action_name: str = None):
    try:
        print("动作:"+ str(action_name))
        if action_name is None:
            raise ValueError("No figure ID provided")
        else:
            action_file = action_name + ".py"
            print(f"The file to call: {action_file}")
            return action_file
    except ValueError as ve:
        print(ve)
        return str(ve)
    except Exception as e:
        print("An unexpected error occurred:", e)
        return "An unexpected error occurred"


# Main program
if __name__ == "__main__":
    import os
    from dotenv import load_dotenv, find_dotenv
    load_dotenv(find_dotenv(), override=True)
    st.set_page_config(
    page_title="HenryAI - Chatbot With Image",
    page_icon="🏠",
    )

    st.subheader("下达机械臂指令")
    from langchain_community.document_loaders import JSONLoader

    
    # Define questions
    questions = {
        'question1': '请你挥挥手',
        'question2': '你能点点头吗',
        'question3': 'Can you rotate around',
        'question4': 'Can you jump? ',
        'question5': '眨眨眼吧',
        'question5': '你能讲话不',
    }
    # Create buttons dynamically and handle clicks
    for question_key, question_text in questions.items():
        if st.button(question_text):
            handle_button_click(question_key)

    if "history" not in st.session_state:
        st.session_state.history = []

    # User input for the question
    # Display chat messages from history on app rerun
    for history in st.session_state.history:
        with st.chat_message(history["role"]):
            st.markdown(history["action"])

    # Check if a question was clicked
    if clicked_question := st.session_state.get('clicked_question'):
        process_question(questions[clicked_question])

    # Handle chat input
    if prompt := st.chat_input("Your Question:"):
# Ensure to reset any clicked question status before processing
        st.session_state.clicked_question = None
        process_question(prompt)