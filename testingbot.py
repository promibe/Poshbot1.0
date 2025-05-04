# -------------------------------------------------------- LIBRARIES -----------------------------------------------
import pickle
import spacy
import numpy as np
import logging
from datetime import datetime
import json
from spacy.pipeline import EntityRuler
import re
from spacy.matcher import Matcher
import dateparser
import requests
import sys


# Load the saved pipeline
with open("intent_classifier.pkl", "rb") as f:
    loaded_pipeline = pickle.load(f)

# Set up logging to file
logging.basicConfig(
    filename='chat_log.json',
    level=logging.INFO,
    format='%(message)s'
)


# -------------------------------------------------------- DATA ----------------------------------------------------
# Intent mapping
target_response = {
    0: 'greetings',
    1: 'enrollment',
    2: 'pricing',
    3: 'tracking',
    4: 'fallback'
}

# Response templates
fallback_responses = [
    "Sorry, I didn’t quite understand that. Can you rephrase, read my previous prompt and respond accordingly?",
    "Hmm, I'm not sure what you mean. Try asking about enrollment or pricing, read my previous prompt and respond accordingly.",
    "Let’s try that again. Ask about courses, prices, or tracking progress, read my previous prompt and respond accordingly"
]

response = {
    'greetings': [
        "Nice, you are very much welcome to Poshem! What do you want to do?\n"
        "- Do want to enroll/register for a course?\n- Check the price of our courses?\n- Confirm your registered courses?"
    ],
    'enrollment': (
        "Kindly request for the course you want to register in this format:\n"
        "(e.g.) I am Promise, born on (YYYY-MM-DD), B-Tech Computer Science.\n"
        "phone number: 07063083925.\n"
        "email address: promise@x.com\n"
        "I want to learn Excel."
    ),
    'pricing': "Our pricing varies by course. Here is the breakdown...",
    'tracking': "To track your course, kindly let me know your ID.",
    'fallback': fallback_responses
}

#---------------------------------------------------------USER PROFILE EXTRACTOR-----------------------------------------
# Load spaCy model
nlp = spacy.load('en_core_web_lg')

# Initialize EntityRuler
ruler = EntityRuler(nlp, overwrite_ents=True)

# Remove default NER to use custom recognition
if "ner" in nlp.pipe_names:
    nlp.remove_pipe("ner")

# Add EntityRuler for course and email
ruler = nlp.add_pipe("entity_ruler", first=True)

# Define custom course list
courses = [
    "excel", "powerbi", "sql", "postgresql", "python for beginners",
    "advance python for data analysis", "python for data analysis",
    "data science", "machine learning",
    "database administrator", "azure devops", "aws devops"
]

course_patterns = [{"label": "COURSE", "pattern": course} for course in courses]
email_patterns = [{"label": "EMAIL", "pattern": [{"LIKE_EMAIL": True}]}]
ruler.add_patterns(course_patterns + email_patterns)

# Add Matcher for name, DOB, qualification, and phone
matcher = Matcher(nlp.vocab)

matcher.add("NAME", [[
    {"LOWER": "i"},
    {"LOWER": "am"},
    {"IS_TITLE": True, "OP": "+"}
]])

matcher.add("DOB", [[
    {"LOWER": "born"},
    {"LOWER": "on"},
    {"IS_TITLE": True, "OP": "+"},
    {"TEXT": {"REGEX": r"^\d{1,2}(st|nd|rd|th)?$"}, "OP": "?"},
    {"IS_DIGIT": True, "OP": "?"}
]])

matcher.add("PHONE", [[
    {"LOWER": "phone"},
    {"LOWER": "number"},
    {"IS_PUNCT": True, "OP": "?"},
    {"TEXT": {"REGEX": r"^\d{11}$"}}
]])

matcher.add("QUALIFICATION", [[
    {"TEXT": {"REGEX": r"^[A-Z][-.A-Za-z]+$"}} ,
    {"IS_TITLE": True, "OP": "+"}
]])


#-------------------------------------------------------------------BOT FUNCTIONS-----------------------------------------

# Function to simulate intent prediction
def user_input_to_model(user_input):
    vector = nlp(user_input).vector
    predicted_intent = loaded_pipeline.predict([vector])[0]  # Extract single prediction
    return predicted_intent

# Function to generate bot response
def response_function(user_intent):
    intent_label = target_response.get(user_intent, 'fallback')

    if intent_label == 'fallback':
        return np.random.choice(response['fallback'])

    reply = response.get(intent_label)
    return reply[0] if isinstance(reply, list) else reply

# Chat history logging function
def log_interaction(user_input, predicted_intent, bot_response):
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "user_input": user_input,
        "predicted_intent": target_response.get(predicted_intent, 'fallback'),
        "bot_response": bot_response
    }
    logging.info(json.dumps(log_entry))


#-----------------------------------------------------------------USER EXTRACTION FUNCTION-------------------------------------

# Function to extract profile data from user input
def extract_profile(user_input):
    doc = nlp(user_input)

    # Apply matcher
    matches = matcher(doc)

    # Initialize extracted data
    name, dob, qualification, phone_number, email, course_ordered = None, None, None, None, None, None

    # Process matches
    for match_id, start, end in matches:
        span = doc[start:end]
        label = nlp.vocab.strings[match_id]

        if label == "NAME":
            name = span.text.replace("I am", "").strip()
        elif label == "DOB":
            dob = span.text.replace("born on", "").strip()
        elif label == "QUALIFICATION":
            qualification = span.text
        elif label == "PHONE":
            phone_number = span[-1].text

    # Extract email & course via ruler
    for ent in doc.ents:
        if ent.label_ == "EMAIL":
            email = ent.text
        elif ent.label_ == "COURSE":
            course_ordered = ent.text

    return name, dob, qualification, phone_number, email, course_ordered

# Function to send user data to the database
def send_user_data_to_db(name, dob, qualification, phone_number, email, course_ordered):
    # Convert date of birth to the proper format (YYYY-MM-DD)
    dob_parsed = dateparser.parse(dob)
    if dob_parsed is None:
        print("❌ Invalid date format. Please try a format like '8th January 1995'")
        sys.exit()

    # Prepare the user data payload
    user_payload = {
        "name": name,
        "dob": dob_parsed.date().isoformat(),  # Ensure date format is 'YYYY-MM-DD'
        "qualification": qualification,
        "phone_number": phone_number,
        "email": email
    }

    # Send POST request to FastAPI to create the user
    user_url = "http://127.0.0.1:8000/users/"  # FastAPI endpoint for user creation
    try:
        user_response = requests.post(user_url, json=user_payload)
        user_response.raise_for_status()
        user_data = user_response.json()
        print(f"✅ User successfully added with User ID: {user_data['user_id']}")

        # Now, create a course order using the user_id from the response
        # Directly create the course order without needing a separate order URL
        order_payload = {
            "user_id": user_data['user_id'],  # Link the order to the newly created user
            "order_details": course_ordered
        }

        # Create order using the same FastAPI endpoint (same as used for user creation)
        order_url = "http://127.0.0.1:8000/orders/"  # FastAPI endpoint for creating order
        order_response = requests.post(order_url, json=order_payload)
        order_response.raise_for_status()
        order_data = order_response.json()
        print(f"✅ Order successfully added with Order ID: {order_data['order_id']}")

    except requests.exceptions.RequestException as e:
        print(f"❌ Error sending request: {e}")
        sys.exit()


#--------------------------------------------------------POSHBOT------------------------------------------------
def Poshbot():
    print("Bot 🤖: Hello! Welcome to Poshem Technologies, a fair greeting will be okay for us to attend to you:")

    in_registration = False
    completed_registration = False
    predicted_intent = None

    while True:
        user_input = input("You 🫥: ").strip()

        if user_input.lower() in ["i am done", "exit", "quit"]:
            print("Bot 🤖: Thanks for choosing Poshem Technologies Institution. This is your course ID. You'll get a mail from us shortly.")
            break

        try:
            # Step 1: If user is in registration mode, extract profile
            if in_registration and not completed_registration:
                try:
                    name, dob, qualification, phone_number, email, course_ordered = extract_profile(user_input)

                    print("Bot 🤖: Thank you! Here's your profile:")
                    print(f"Name: {name}")
                    print(f"DOB: {dob}")
                    print(f"Qualification: {qualification}")
                    print(f"Phone: {phone_number}")
                    print(f"Email: {email}")
                    print(f"Course: {course_ordered}")

                    print("Bot 🤖: Your registration is complete! ✅")

                    # Call the function to send the user and order data to the backend
                    send_user_data_to_db(name, dob, qualification, phone_number, email, course_ordered)

                    print("Bot 🤖: What else do you want to do, else kindly quite, exit or say you are done!!!")

                    completed_registration = True
                    in_registration = False  # Reset flag
                    predicted_intent = None  # Clear intent

                    continue  # Go back to next user input
                except Exception as e:
                    print("Bot 🤖: Sorry, I couldn't extract your enrollment details. Please try again.")
                    continue

            # Step 2: Predict intent if not in registration
            predicted_intent = user_input_to_model(user_input)
            bot_response = response_function(predicted_intent)

            print(f"Bot 🤖: {bot_response}")

            # Step 3: If intent is enrollment, set the flag
            if predicted_intent == 1:  # Or 'enrollment' depending on how your model works
                in_registration = True
                continue

            # Step 4: Handle other general replies
            log_interaction(user_input, predicted_intent, bot_response)

        except Exception as e:
            print("Bot 🤖: Sorry, I couldn't process that. Please try again.")

Poshbot()

