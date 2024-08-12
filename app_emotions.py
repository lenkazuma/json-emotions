#OpenAI/FC/Sales_Assist/CN

import streamlit as st
from openai import OpenAI
from langchain_openai import ChatOpenAI
from langchain_community.callbacks import get_openai_callback
import time
import os
import asyncio
import json
import urllib.request
from PIL import Image
import io
from streamlit_lottie import st_lottie
import json

# Ensure an event loop is available and set it as the current event loop
loop = asyncio.get_event_loop_policy().new_event_loop()
asyncio.set_event_loop(loop)


animation_list = {
    "Asking": "Asking.json - 3s - 'Which one is .....?'",
    "characterIntro": "characterIntro.json - 7s - 'Hello, I am Mrs Fox, I am from Australia, I will be your tutor'",
    "congratulation": "congratulation.json - 5s - 'Wonderful, you have completed the chapter'",
    "correct1": "correct1.json - 3s - 'You are correct!'",
    "correct2": "correct2.json - 3s - 'Great Job'",
    "wrong1": "wrong1.json - 3s - 'Try again, you can do it'",
    "wrong2": "wrong2.json - 3s - 'Let’s try again'"
}
llm = ChatOpenAI(
    model_name="gpt-4o",
    streaming=True
)

#general ask without using vectorstore,no rag
def ask_general(question):
    client=OpenAI()

    response = client.chat.completions.create(
        model="gpt-4o",  # Adjust to the latest available GPT-4 model
        temperature= 0.1,
        messages=[
            {"role": "system", "content": "You are a helpful assistant that kindly answers the question to any topic."},
            {"role": "user", "content": question}
        ]
    )
    return response.choices[0].message.content

# Simplify button clicks handling
def handle_button_click(question_key):
    st.session_state.clicked_question = question_key

def stream_data(answer):
    for word in answer.split():
        yield word + " "
        time.sleep(0.1)




# Process and display the question and answer
def process_question(question):
    # Add user message to chat history
    with st.chat_message("user"):
            st.markdown(question)
    st.session_state.history.append({"role": "user", "content": question})

    answer = ask_general(question)
    # Display assistant response in chat message container
    with st.chat_message("assistant"):
        st.markdown(answer)
        prompt = f'''
        Based on the content or tone of the provided context, select the most appropriate animation from the list below. The selected animation should accurately reflect the nature of the response, whether it’s an introduction, a question, a correct answer, an incorrect answer, or a congratulation.
        Animation list:
        - Asking: {animation_list['Asking']}
        - Character Introduction: {animation_list['characterIntro']}
        - Congratulations: {animation_list['congratulation']}
        - Correct Answer 1: {animation_list['correct1']}
        - Correct Answer 2: {animation_list['correct2']}
        - Wrong Answer 1: {animation_list['wrong1']}
        - Wrong Answer 2: {animation_list['wrong2']}

        Context: {answer}
        '''
        messages = [{"role": "user", "content": prompt}]
        response_message = fc_call(messages)  # Pass as list if not already handled
        img = None  # Default result to None to handle exceptions
        #st.write(response_message)
        try:
            # Which function call was invoked
            function_called = response_message.function_call.name
            # Extracting the arguments
            function_args  = json.loads(response_message.function_call.arguments)
            # Function names
            available_functions = {'get_animation': get_animation}
            function_to_call = available_functions[function_called]
            image_data = function_to_call(*list(function_args.values()))
            #st.write("FC Success")
            if image_data:
                url = image_data["items"][0]["link"]
                #st.write(url)
                img = Image.open(io.BytesIO(urllib.request.urlopen(url).read()))
                st.image(img)

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
    st.session_state.history.append({"role": "assistant", "content": answer,"score":user_feedback,"image":img})
# Reset clicked_question to prevent it from affecting subsequent actions
st.session_state.clicked_question = None


## ======================================
## Function call related
## ======================================
function_call_limit = 3
def fc_call(messages):
    client = OpenAI()
    # Ensure messages is a list
    if not isinstance(messages, list):
        messages = [messages]
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        temperature=0.1,
        functions=[
            {
                "name": "get_animation",
                "description": "Retrieve the animation",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "fig_id": {
                            "type": "string",
                            "description": "The image number, which should be an integer ranging from 1 to 32."
                        }
                    },
                    "required": ["fig_id"]
                },
                 "responses": {
                    "type": "object",
                    "properties": {
                        "figure_file_location": {
                            "type": "integer",
                            "description": "The file path of the retrieved image."
                        }
                    }
                }
            }
        ],
        function_call = 'auto'
    )
    return response.choices[0].message

def get_animation(fig_id: str = None):
    st.write("动画文件:"+ str(fig_id)+".json")
    try:
        if fig_id is None:
            raise ValueError("No figure ID provided")
        else:
            with open(f"./animation/{fig_id}.json", "r",errors='ignore') as f:
                data = json.load(f)
            st_lottie(data)
    except Exception as e:
        print("An unexpected error occurred:", e)
        return None

# Main program
if __name__ == "__main__":
    import os
    from dotenv import load_dotenv, find_dotenv
    load_dotenv(find_dotenv(), override=True)
    st.set_page_config(
    page_title="HenryAI - Chatbot With Image",
    page_icon="🏠",
    )

    st.subheader("AI Chat with Lottie animation")

    # Define questions
    questions = {
        'question1': '13.8比13.11大吗？',
        'question2': '能介绍一下你自己吗？',
        'question3': '我觉得宇宙是无边界的，你说对吗？',
        'question4': '1+1=3，对吗？',
        'question5': '能恭喜一下我吗'
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