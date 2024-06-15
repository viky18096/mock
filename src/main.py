import streamlit as st
import pandas as pd
import speech_recognition as sr
import openai
import os

# Get the OpenAI API key from environment variables
openai.api_key = os.getenv("OPENAI_API_KEY")

def load_questions(file_path):
    df = pd.read_csv(file_path)
    return df["questions"].tolist()

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

def get_ai_response(transcribed_text):
    response = openai.Completion.create(
        engine="davinci",
        prompt=transcribed_text,
        max_tokens=150
    )
    return response.choices[0].text.strip()

def save_transcript(question, user_response, ai_response):
    data_dir = "../data"
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)

    transcript_file_path = os.path.join(data_dir, "transcripts.csv")
    if not os.path.exists(transcript_file_path):
        with open(transcript_file_path, "w") as f:
            f.write("Question,User Response,AI Response\n")
    with open(transcript_file_path, "a") as f:
        f.write(f"{question},{user_response},{ai_response}\n")

def display_transcripts():
    if os.path.exists("../data/transcripts.csv"):
        df = pd.read_csv("../data/transcripts.csv")
        st.subheader("Saved Transcripts")
        st.dataframe(df)
    else:
        st.write("No transcripts found.")

def main():
    st.title("AI-based Mock Interview Practice")

    # Load questions from the master question booklet
    questions = load_questions("../data/questions.csv")
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
                ai_response = get_ai_response(transcribed_text)
                st.write("AI Response: ", ai_response)
                
                save_transcript(current_question, transcribed_text, ai_response)
                st.success("Transcript saved successfully.")
    
    display_transcripts()

if __name__ == "__main__":
    main()
