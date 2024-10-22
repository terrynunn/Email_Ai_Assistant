import os
import json
from openai import OpenAI

# Initialize the OpenAI client
client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

# Load the assistant configuration
with open("assistant_config.json", "r") as config_file:
    assistant_config = json.load(config_file)

# Create the assistant
assistant = client.beta.assistants.create(**assistant_config)

def search_documentation(query, language):
    # This is a placeholder function. In a real implementation,
    # you would integrate with actual documentation search APIs.
    if language == "wolfram":
        return "To search for help in Wolfram, use the Documentation Center accessible from the Help menu. You can also use online resources at reference.wolfram.com. For specific functions, type a question mark before the function name in a notebook."
    elif language == "unity":
        return "For Unity documentation, you can access offline docs by installing the Documentation module through Unity Hub. You can also add it as a search engine in your browser for quick access."
    else:
        return f"Searching for '{query}' in {language} documentation..."

# Function to run the assistant
def run_assistant(user_input):
    # Create a thread
    thread = client.beta.threads.create()

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
                if tool_call.function.name == "search_documentation":
                    arguments = json.loads(tool_call.function.arguments)
                    output = search_documentation(**arguments)
                    client.beta.threads.runs.submit_tool_outputs(
                        thread_id=thread.id,
                        run_id=run.id,
                        tool_outputs=[{
                            "tool_call_id": tool_call.id,
                            "output": json.dumps(output)
                        }]
                    )

    # Retrieve and return the assistant's response
    messages = client.beta.threads.messages.list(thread_id=thread.id)
    return messages.data[0].content[0].text

# Example usage
if __name__ == "__main__":
    user_input = "How do I search for help in Wolfram?"
    response = run_assistant(user_input)
    print(response)
