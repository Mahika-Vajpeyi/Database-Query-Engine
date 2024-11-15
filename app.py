from dotenv import load_dotenv
import os
import google.generativeai as genai 
import sqlite3
import streamlit as st
import pandas as pd
import re

load_dotenv()

system_prompt=("""
I have an sqlite database with the following table and columns:
Table name: RatePlan
Columns:
* RatePlanId INTEGER PRIMARY KEY
* Name VARCHAR(255)
* MonthlyFee FLOAT
* CallRate FLOAT
* SmsRate FLOAT
* DataRate FLOAT
        
Table name: Customer
Columns:
* CustomerId INTEGER PRIMARY KEY
* FirstName VARCHAR(255)
* LastName VARCHAR(255)
* Address VARCHAR(255)
* City VARCHAR(255)
* State VARCHAR(255)
* Country VARCHAR(255)
* PostalCode VARCHAR(255)
* Phone VARCHAR(255)
* Email VARCHAR(255)
* RatePlanId INT, FOREIGN KEY (RatePlanId) REFERENCES RatePlan(RatePlanId)
* ContractStart DATE
* ContractEnd DATE
        
Table name: Phone
Columns:
* PhoneId INTEGER PRIMARY KEY
* Brand VARCHAR(255)
* Model VARCHAR(255)
* OS VARCHAR(255)
* Price FLOAT
        
Table name: CustomerPhone
Columns:
* CustomerPhoneId INTEGER PRIMARY KEY
* CustomerId INT, FOREIGN KEY (CustomerId) REFERENCES Customer(CustomerId)
* PhoneId INT, FOREIGN KEY (PhoneId) REFERENCES Phone(PhoneId)
* PhoneAcquisitionDate DATE
        
Table name: CDR
Columns:
* CdrId INTEGER PRIMARY KEY
* CustomerId INT, FOREIGN KEY (CustomerId) REFERENCES Customer(CustomerId)
* PhoneNumber VARCHAR(255)
* CallDateTime DATETIME
* CallType VARCHAR(255)
* DurationInSeconds INT
* DataUsageKb INT
* SmsCount INT

I will need you to help me generate SQL queries to get data from my database.

Please respond only with the query. Do not provide any explanations or additional text.
""")

history = [
    {"role": "user", "parts": system_prompt}, 
    {"role": "model", "parts": "Acknowledged"}
]

if "model" not in st.session_state:
    print("instantiating model")
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
    st.session_state.model=genai.GenerativeModel('gemini-1.5-flash')
    st.session_state.chat = st.session_state.model.start_chat(history=history)

def get_gemini_response(user_query):
    response = st.session_state.chat.send_message(user_query)
    return response.text

def get_sql_response(sql_query, retries = 2):
    # execute SQL queries
    extracted_query = extract_sql_query(sql_query)

    #print message if query tries to modify the database
    if re.match(r"^\s*(drop|alter|truncate|delete|insert|update)\s", extracted_query, re.I):
        print("SQL query has forbidden order")
        return [],[], "Sorry, I can't execute queries that modify the database."
   
    # connect to the db
    conn = sqlite3.connect(
        database=os.getenv("DB_NAME")
    )

    # create a cursor object
    cur = conn.cursor()
    # Check if the cursor is instantiated correctly
    if cur is None:
        print("Failed to create cursor object.")
    else:
        print("Cursor object instantiated correctly.")

    try:
        cur.execute(extracted_query)
        rows = cur.fetchall()
        conn.commit()
        conn.close()

        # Get column names
        columns = [desc[0] for desc in cur.description]

        return columns, rows, ""
    except Exception as e:
        return handle_sql_exception(extracted_query, e, retries)
            
def extract_sql_query(text):
    sql_match = re.search(r"```sql\n(.*)\n```", text, re.DOTALL)
    return sql_match.group(1) if sql_match else None

    # start_index = text.find("```sql") + len("```sql")
    # end_index = text.find("```", start_index)
    # sql_query = text[start_index:end_index].strip()
    # return sql_query

def handle_sql_exception(extracted_query, error_message, retries):
    print("in handle exception")
    with st.chat_message("assistant"):
        st.markdown("Trying to fix the error")
    
    error_message = (
        "You gave me an incorrect query. Fix the SQL query:  \n```sql\n"
        + extracted_query + "\n "
        + "DO NOT MODIFY THE USER QUERY \n "
        + "\n```\n Error message: \n "
        + str(error_message)
    )
    corrected_query = get_gemini_response(error_message)
    print("corrected query ", corrected_query)
    # st.session_state.messages.append({"role": "assistant", "content": corrected_query})
    with st.chat_message("assistant"):
        print("printing corrected query ")
        st.markdown(corrected_query)

    if retries > 0:
        return get_sql_response(corrected_query, retries-1)
    else:
        explanation = "Could not fix the query"
        return [], [], explanation
    
# Creating a Streamlit app
st.title("SQL Generator")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Initialize DataFrame history
if "df_history" not in st.session_state:
    st.session_state.df_history = []
    
# Display chat messages from history on app rerun
for i in range(len(st.session_state.df_history)):
     #if role is user, write content else write df or explanation
    with st.chat_message(st.session_state.messages[i]["role"]):
        st.markdown(st.session_state.messages[i]["content"])
    with st.chat_message("assistant"):
        if isinstance(st.session_state.df_history[i], pd.DataFrame):
            st.write(st.session_state.df_history[i])
        else:
            st.markdown(st.session_state.df_history[i]["content"])

# Accept user input
question = st.chat_input("Say something")

if question:
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": question})
    # Display user message in chat message container
    with st.chat_message("user"):
        st.markdown(question)

    print("user input: ", question)
    response = get_gemini_response(question)

    print("gemini query: " + response)
    columns, rows, explanation = get_sql_response(response)

    if len(explanation) != 0: 
        st.session_state.df_history.append({"role": "assistant", "content": explanation})
        with st.chat_message("assistant"):
            st.markdown(explanation)
    else:
        df = pd.DataFrame(rows, columns=columns)
        st.session_state.df_history.append(df)
        with st.chat_message("assistant"):
            st.write(df)