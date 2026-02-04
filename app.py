from openai import OpenAI
import streamlit as st
from streamlit_js_eval import streamlit_js_eval
from ingestion import ingest
from retrieval import retrieve
st.set_page_config(page_title="Interview Simulator", page_icon="🤖")
st.title("Interview Simulator")

if "setup_complete" not in st.session_state:
    st.session_state.setup_complete = False
if "user_message_count" not in st.session_state:
    st.session_state.user_message_count = 0
if "feedback_shown" not in st.session_state:
    st.session_state.feedback_shown = False
if "messages" not in st.session_state:
    st.session_state["messages"] = []
if "chat_completed" not in st.session_state:
    st.session_state["chat_completed"] = False
if "HR_question" not in st.session_state:
    st.session_state.HR_question = False

# Initialize session state for HR chat
if "hr_user_message_count" not in st.session_state:
    st.session_state.hr_user_message_count = 0
if "hr_chat_completed" not in st.session_state:
    st.session_state["hr_chat_completed"] = False
if "hr_messages" not in st.session_state:
    st.session_state["hr_messages"] = []


def complete_setup():
    st.session_state.setup_complete = True

def show_feedback():
    st.session_state.feedback_shown = True
def hide_feedback():
    st.session_state.feedback_shown = False

if not st.session_state.setup_complete:
    st.subheader("Personal information", divider = "rainbow")
    if "name" not in st.session_state:
        st.session_state["name"] = ""
    if "experience" not in st.session_state:
        st.session_state["experience"] = ""
    if "skills" not in st.session_state:
        st.session_state["skills"] = ""
    
    st.session_state["name"] = st.text_input(label="Name", value = st.session_state["name"], max_chars=20, placeholder="Your name here")
    st.session_state["experience"] = st.text_area(label="Experience", max_chars=40, value = st.session_state["experience"], placeholder="Your experience here")
    st.session_state["skills"] = st.text_area(label="Skills", value = st.session_state["skills"], placeholder="Your skills here")

    st.subheader("Company and position", divider = "rainbow")

    if "level" not in st.session_state:
        st.session_state["level"] = "Intern"
    if "position" not in st.session_state:
        st.session_state["position"] = "Software Engineer"
    if "company" not in st.session_state:
        st.session_state["company"] = "Google"

    col1, col2 = st.columns(2)
    with col1:
        st.session_state["level"] = st.radio(label="Level", 
                        key = "visibility",
                        options=["Intern", "Junior", "Mid", "Senior", "Lead"])

    with col2:
        st.session_state["position"] = st.selectbox(label="Position", 
                                options=["Software Engineer", "Data Scientist", "Product Manager", "Designer", "DevOps Engineer"])

    st.session_state["company"] = st.selectbox(label="Company",
                            options=["Google", "Amazon", "Facebook", "Apple", "Microsoft", "Netflix", "Other"])


    if st.button("Start Interview", on_click=complete_setup):
        st.write("Setup complete ,Interview started!")

if st.session_state.setup_complete and not st.session_state.chat_completed and not st.session_state.feedback_shown:

    # st.info("You can change the personal information and company/position details by modifying the fields above.", icon="ℹ️")
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

    if "openai_model" not in st.session_state:
        st.session_state["openai_model"] = "gpt-3.5-turbo"


    # The messages key stores the entire history of our chat, including all messages sent by the user and the assistant.
    # It acts as a container that keeps track of the conversation as it evolves.

    if not st.session_state.messages:
        st.session_state.messages = [{"role": "system", "content": f"You are a helpful HR executive that interviews an interviewee called {st.session_state['name']} for the position of {st.session_state['level']} {st.session_state['position']} at {st.session_state['company']}. The interviewee has the following experience: {st.session_state['experience']} and the following skills: {st.session_state['skills']}. Ask relevant interview questions based on the provided information."}]

    for message in st.session_state.messages:
        if message["role"] != "system":
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    if st.session_state.user_message_count < 5:
        if prompt := st.chat_input("Your answer here:", max_chars=200):
            st.session_state.messages.append({"role": "user", "content": prompt})

            with st.chat_message("user"):
                st.markdown(prompt)

        # We first use the with statement to create a context block.This is followed by the chat message method in which we pass the string assistant as an argument.
        #This creates a dedicated block to display the assistance response in the chat interface.

        #Next, we call the OpenAI API to generate the assistance response.

        #The OpenAI create function used here takes several parameters.

        #The first is model, which specifies the model we're using, which we defined earlier as GPT four.

            
            if st.session_state.user_message_count < 4:
                with st.chat_message("assistant"):
                    stream = client.chat.completions.create(
                        model=st.session_state["openai_model"],
                        messages=[
                            {"role": m["role"], "content": m["content"]}
                            for m in st.session_state.messages
                        ],
                        stream=True,
                    )
                    response = st.write_stream(stream)
                st.session_state.messages.append({"role": "assistant", "content": response})
            st.session_state.user_message_count += 1
    if st.session_state.user_message_count >= 5:
        st.session_state.chat_completed = True

if st.session_state.chat_completed and not st.session_state.feedback_shown and not st.session_state.HR_question:
    if st.button("Get Feedback", on_click=show_feedback):
        st.write("Fetching feedback!")

if st.session_state.feedback_shown and not st.session_state.HR_question:
    st.subheader("Interview Feedback", divider = "rainbow")
    conversation_history = "\n".join([f"{msg['role']}: {msg['content']}" for msg in st.session_state.messages if msg['role'] != 'system'])

    feedback_client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
    feedback_response = feedback_client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": """You are a helpful tool that provides feedback on an interviewee performance.
             Before the Feedback give a score of 1 to 10.
             Follow this format:
             Overal Score: //Your score
             Feedback: //Here you put your feedback
             Give only the feedback do not ask any additional questins.
              """},
            {"role": "user", "content": f"This is the interview you need to evaluate. Keep in mind that you are only a tool. And you shouldn't engage in any converstation: {conversation_history}"}
        ]
    )
    st.write(feedback_response.choices[0].message.content)


    if st.button("Restart Interview", type="primary"):
        streamlit_js_eval(js_expressions="parent.window.location.reload()")
    
    def _ask_hr_question():
        st.session_state.HR_question = True
        st.session_state.feedback_shown = False

    st.button("Click here if you have a question?", on_click=_ask_hr_question)



if st.session_state.HR_question:
    st.subheader("Ask HR Question", divider = "rainbow")
    ingest("HR_Policy_1.docx")

    

    if not st.session_state.hr_messages:
        st.session_state.hr_messages = [{"role": "system", "content": f"""you are a helpful HR executive who is answering questions for an intervieweeabout HR policies of the company {st.session_state['company']}. 
                                         Refer the company policies document while answering the questions. If you don't know the answer, simply state that you don't have that information.

                                         """}]
    for message in st.session_state.hr_messages:
        if message["role"] != "system":
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    if st.session_state.hr_user_message_count < 4:
        if prompt := st.chat_input("Your question here:", max_chars=200):
            st.session_state.hr_messages.append({"role": "user", "content": prompt})

            with st.chat_message("user"):
                st.markdown(prompt)

            
            if st.session_state.hr_user_message_count < 4:
                with st.chat_message("assistant"):
                    response = retrieve(prompt)
                    st.markdown(response)
                st.session_state.hr_messages.append({"role": "assistant", "content": response})
            st.session_state.hr_user_message_count += 1
    if st.session_state.hr_user_message_count >= 4:
        st.session_state.hr_chat_completed = True
        
    if st.button("Restart Interview", type="primary"):
        streamlit_js_eval(js_expressions="parent.window.location.reload()")
