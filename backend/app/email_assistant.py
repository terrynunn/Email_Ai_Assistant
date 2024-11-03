import os
import json
from dotenv import load_dotenv
from openai import OpenAI
from msal import PublicClientApplication
import requests

# Load environment variables from .env file
load_dotenv()

# Initialize the OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Microsoft Graph API settings
CLIENT_ID = os.getenv("MS_GRAPH_CLIENT_ID")
CLIENT_SECRET = os.getenv("MS_GRAPH_CLIENT_SECRET")
TENANT_ID = os.getenv("MS_GRAPH_TENANT_ID")
GRAPH_API_ENDPOINT = 'https://graph.microsoft.com/v1.0'

# Get the directory where the current script is located
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Load the assistant configuration using absolute path
with open(os.path.join(SCRIPT_DIR, "assistant_config.json"), "r") as config_file:
    assistant_config = json.load(config_file)

# Create the assistant
assistant = client.beta.assistants.create(**assistant_config)

def get_access_token():
    app = PublicClientApplication(
        CLIENT_ID,
        authority=f"https://login.microsoftonline.com/{TENANT_ID}"
    )
    
    scopes = ["https://graph.microsoft.com/Mail.Read"]
    
    result = None
    accounts = app.get_accounts()
    if accounts:
        result = app.acquire_token_silent(scopes, account=accounts[0])
    
    if not result:
        flow = app.initiate_device_flow(scopes=scopes)
        if "user_code" not in flow:
            raise Exception("Failed to create device flow")
        
        print(flow["message"])
        
        result = app.acquire_token_by_device_flow(flow)
    
    if "access_token" in result:
        return result["access_token"]
    else:
        raise Exception(f"Failed to obtain access token: {result.get('error_description')}")

def search_emails(query, top=10, select=None):
    print(f"Debug: Search query: {query}")
    print(f"Debug: Top: {top}")
    print(f"Debug: Select: {select}")
    
    access_token = get_access_token()
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    if select is None:
        select = ["subject", "from", "receivedDateTime", "bodyPreview"]
    
    select_param = ",".join(select)
    url = f"{GRAPH_API_ENDPOINT}/me/messages?$search=\"{query}\"&$top={top}&$select={select_param}"
    
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json().get('value', [])
    else:
        raise Exception(f"Error searching emails: {response.status_code} - {response.text}")

# Function to run the assistant
def run_assistant(user_input):
    thread = client.beta.threads.create()

    client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=user_input
    )

    run = client.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=assistant.id
    )

    while run.status != "completed":
        run = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
        if run.status == "requires_action":
            for tool_call in run.required_action.submit_tool_outputs.tool_calls:
                if tool_call.function.name == "search_emails":
                    arguments = json.loads(tool_call.function.arguments)
                    print(f"Debug: search_emails arguments: {arguments}")
                    output = search_emails(**arguments)
                    client.beta.threads.runs.submit_tool_outputs(
                        thread_id=thread.id,
                        run_id=run.id,
                        tool_outputs=[{
                            "tool_call_id": tool_call.id,
                            "output": json.dumps(output)
                        }]
                    )

    messages = client.beta.threads.messages.list(thread_id=thread.id)
    return messages.data[0].content[0].text.value

# Function to handle the conversation
def chat_with_assistant():
    print("Welcome to the Email Search Assistant!")
    print("You can ask questions about your emails or request searches.")
    print("Type 'quit' to exit the chat.")
    
    thread = client.beta.threads.create()
    
    while True:
        user_input = input("\nYou: ")
        if user_input.lower() == 'quit':
            print("Goodbye!")
            break
        
        # Add the user's message to the thread
        client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=user_input
        )
        
        # Run the assistant
        run = client.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=assistant.id
        )
        
        # Wait for the run to complete
        while run.status != "completed":
            run = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
            if run.status == "requires_action":
                for tool_call in run.required_action.submit_tool_outputs.tool_calls:
                    if tool_call.function.name == "search_emails":
                        arguments = json.loads(tool_call.function.arguments)
                        print(f"Debug: search_emails arguments: {arguments}")
                        output = search_emails(**arguments)
                        client.beta.threads.runs.submit_tool_outputs(
                            thread_id=thread.id,
                            run_id=run.id,
                            tool_outputs=[{
                                "tool_call_id": tool_call.id,
                                "output": json.dumps(output)
                            }]
                        )
        
        # Retrieve and print the assistant's response
        messages = client.beta.threads.messages.list(thread_id=thread.id)
        assistant_message = next((m for m in messages if m.role == "assistant"), None)
        if assistant_message:
            print("\nAssistant:", assistant_message.content[0].text.value)
        else:
            print("\nAssistant: I'm sorry, I couldn't generate a response.")

def get_assistant_response(message):
    """
    Wrapper function to handle a single message and return response
    """
    try:
        return run_assistant(message)
    except Exception as e:
        return f"Error: {str(e)}"
