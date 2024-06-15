import streamlit as st
import pandas as pd
import speech_recognition as sr
import openai
import os

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


# Get the OpenAI API key from environment variables
openai.api_key = os.getenv("OPENAI_API_KEY")


# Function to load questions from a file
def load_questions(file_path):
    try:
        if file_path.endswith('.csv'):
            df = pd.read_csv(file_path, encoding='utf-8')
        elif file_path.endswith('.xlsx'):
            df = pd.read_excel(file_path)
        else:
            st.error("Unsupported file format. Please use a CSV or Excel file.")
            return None
        st.write("Loaded Questions DataFrame:")
        st.write(df.head())  # Print the DataFrame to debug
        return df
    except FileNotFoundError:
        st.error("File not found. Please ensure the file path is correct.")
        return None
    except Exception as e:
        st.error(f"An error occurred while loading the file: {e}")
        return None

# Function to save new questions to the file
def save_question(file_path, subject, question):
    try:
        if file_path.endswith('.csv'):
            df = pd.read_csv(file_path, encoding='utf-8')
        elif file_path.endswith('.xlsx'):
            df = pd.read_excel(file_path)
        else:
            st.error("Unsupported file format. Please use a CSV or Excel file.")
            return

        new_row = pd.DataFrame({"subject": [subject], "questions": [question]})
        df = pd.concat([df, new_row], ignore_index=True)

        if file_path.endswith('.csv'):
            df.to_csv(file_path, index=False, encoding='utf-8')
        elif file_path.endswith('.xlsx'):
            df.to_excel(file_path, index=False)
    except Exception as e:
        st.error(f"An error occurred while saving the question: {e}")

# Function to record and transcribe audio
def record_and_transcribe():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        st.write("Recording... Please speak clearly into the microphone.")
        try:
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=10)
            st.write("Recording complete.")
            
            # Ensure the recordings directory exists
            recordings_dir = "../recordings"
            if not os.path.exists(recordings_dir):
                os.makedirs(recordings_dir)
            
            # Save the audio file
            audio_file_path = os.path.join(recordings_dir, "response.wav")
            with open(audio_file_path, "wb") as f:
                f.write(audio.get_wav_data())
                
            st.write("Transcribing your response...")
            text = recognizer.recognize_google(audio)
            return text
        except sr.WaitTimeoutError:
            return "Recording timed out. Please try again."
        except sr.UnknownValueError:
            return "Could not understand the audio, please try again."
        except sr.RequestError as e:
            return f"Could not request results from the speech recognition service; {e}"

# Function to get AI response
def get_ai_response(transcribed_text, question):
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
                {"role": "system", "content": "You are an unbiased journalist who verifies politicians' claims/answers. Your aim is to hold them accountable by seeking clarity and truth in their statements. Avoid accepting vague or evasive answers."},
                {"role": "user", "content": f"{transcribed_text} and the question to politicians is increasing"},
            ],
        max_tokens=150
    )
    return response.choices[0].message.content

# Function to save the transcript
def save_transcript(subject, question, user_response, ai_response):
    data_dir = "../data"
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)

    transcript_file_path = os.path.join(data_dir, "transcripts.csv")
    if not os.path.exists(transcript_file_path):
        with open(transcript_file_path, "w", encoding='utf-8') as f:
            f.write("Subject,Question,User Response,AI Response\n")
    with open(transcript_file_path, "a", encoding='utf-8') as f:
        f.write(f"{subject},{question},{user_response},{ai_response}\n")

# Function to display transcripts
def display_transcripts():
    try:
        if os.path.exists("../data/transcripts.csv"):
            df = pd.read_csv("../data/transcripts.csv", encoding='utf-8')
            st.subheader("Saved Transcripts")
            st.dataframe(df)
        else:
            st.write("No transcripts found.")
    except pd.errors.ParserError:
        st.error("Error parsing the transcripts file. Please check the file for inconsistencies.")
    except Exception as e:
        st.error(f"An error occurred while loading the transcripts: {e}")

# Main function for Streamlit app
def main():
    st.title("AI-based Mock Interview Practice")

    # Load questions from the master question booklet
    file_path = r"C:\Users\vikas\Downloads\mock_interview\data\questions.xlsx"
    df = load_questions(file_path)
    if df is None:
        return

    if "subject" not in df.columns:
        st.error("The 'subject' column is missing from the file.")
        return

    subjects = df["subject"].unique()
    selected_subject = st.selectbox("Select a subject", subjects)
    questions = df[df["subject"] == selected_subject]["questions"].tolist()
    current_question = st.selectbox("Select a question", questions)

    if st.button("Start Interview"):
        st.session_state["interview_started"] = True

    if st.session_state.get("interview_started", False):
        st.subheader("Current Question")
        st.write(current_question)
        
        if st.button("Record Answer"):
            transcribed_text = record_and_transcribe()
            st.write("Your Answer: ", transcribed_text)
            
            if transcribed_text and "Could not" not in transcribed_text:
                st.write("Getting AI response...")
                ai_response = get_ai_response(transcribed_text, current_question)
                st.write("AI Response: ", ai_response)

                save_transcript(selected_subject, current_question, transcribed_text, ai_response)
                st.write("Transcript saved successfully.")
    
    st.sidebar.title("Admin Panel")
    if st.sidebar.checkbox("Submit a new question"):
        st.sidebar.subheader("Submit a new question")
        new_subject = st.sidebar.text_input("Subject")
        new_question = st.sidebar.text_area("Question")
        if st.sidebar.button("Submit"):
            save_question(file_path, new_subject, new_question)
            st.sidebar.success("Question submitted successfully!")

    display_transcripts()

if __name__ == "__main__":
    main()
