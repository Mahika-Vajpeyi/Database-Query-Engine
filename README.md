# Database-Query-Engine

### Goal
Since business leaders and other stakeholders may need to access organizational data stored in relational databases but may not be familiar with databases/SQL, I designed a database query engine to make information easily available. The engine accepts text input, representing an information need, entered by the user and fetches relevant results from the underlying database.

### Approach
Step 1: Leverage LLMs to convert natural language into an SQL query
Step 2: Execute the generated query against the database to fetch  and display results 

### Implementation
###### Step 1
Since the Gemini API supports a large free tier, I used Gemini to parse user input and generate an SQL query. I also used the following system prompt to specify the database schema and set the context for the conversation. I also maintained chat history to allow users to follow up on previous messages and make the exchange between the user and assistant more conversational. 

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

###### Step 2
I parsed Gemini’s response to extract the SQL query generated and also built guardrails to preserve the authenticity of the data. Specifically, if the extracted query involved any SQL statements for database modification, namely, DROP, ALTER, TRUNCATE, DELETE, INSERT or UPDATE,  I terminated program execution and displayed a message to the user stating that their request could not be met. 

For all other queries, I fetched results from the database and displayed them as Pandas dataframes in the chat interface designed using Streamlit. To make the engine more robust, I implemented exception handling, that is, if the Gemini-generated SQL query contained errors, the engine would make two attempts to fix the error before responding to the user. 

### Next steps
I tried displaying charts where relevant to the user query. My initial attempt at the logic for displaying charts was two simple checks - whether the results fetched from the database contained only two columns or at least two numeric columns. I tested my engine with some queries whose results would match the criteria mentioned. However, the engine struggled to produce any meaningful results even after several tweaks to chart type and column check. So, a possible next step is to implement more sophisticated logic for displaying charts which would enable the engine to support data analysis in addition to data retrieval.

Additionally, when given a query for extracting information that does not exist in the database such as extracting all distinct sports that customers play, Gemini modifies the query in subsequent attempts. For example, it extracts distinct values from a column that does exist in the Customer table such as Name. Ensuring Gemini does not modify the original information need is, thus, another area for improvement.
