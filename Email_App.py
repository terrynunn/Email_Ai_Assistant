import os
from azure.identity import DeviceCodeCredential
from msgraph_core import GraphClient
# from msgraph_core.requests import GraphRequest
from openai import OpenAI

client_id = ""
tenant_id = ""
scopes = ["User.Read", "Mail.Read", "Mail.Send"]

credential = DeviceCodeCredential(client_id, tenant_id=tenant_id)
graph_client = GraphClient(credential=credential, scopes=scopes)

# Initialize OpenAI client
openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

def process_emails():
    # Fetch recent emails
    request_url = '/me/messages?$top=10&$orderby=receivedDateTime desc'
    response = graph_client.get(request_url)
    emails = response.json().get('value', [])

    for email in emails:
        subject = email['subject']
        body = email['body']['content']

        # Process email with OpenAI
        prompt = f"Summarize this email:\nSubject: {subject}\nBody: {body}"
        completion = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that summarizes emails."},
                {"role": "user", "content": prompt}
            ]
        )

        summary = completion.choices[0].message.content

        print(f"Email: {subject}")
        print(f"Summary: {summary}\n")

if __name__ == "__main__":
    process_emails()
