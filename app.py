import os
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from slack_bolt.adapter.flask import SlackRequestHandler
from slack_bolt import App
from dotenv import find_dotenv, load_dotenv
from flask import Flask, request
import pinecone
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores import Pinecone
from langchain.chains.qa_with_sources import load_qa_with_sources_chain
from langchain.llms import OpenAI
import openai

#loading the environment
load_dotenv(find_dotenv())
openai.api_key = os.environ['OPENAI_API_KEY']

#variables to keep track of both conversation history and direct history
dmHistory = ""
channelHistory = ""

#initializing the server
app = App(token=os.environ["SLACK_BOT_TOKEN"])
flask_app = Flask(__name__)
handler = SlackRequestHandler(app)

#initializing pincone, the vector database
pinecone.init(
    api_key=str(os.environ['PINECONE_API_KEY']),  
    environment=str(os.environ['PINECONE_ENV'])  
)

#obtaining the index within pinecone
index = pinecone.Index(os.environ['PINECONE_INDEX_NAME'])

def queryModel(question, source):
    global dmHistory
    global channelHistory
    #cleaning appropriate conversation history if user wants to move to new topic
    if question == "clear":
        if source == "message":
            dmHistory = ""
        elif source == "channel":
            channelHistory = ""
        return "Cleared!"
    
    #embedding the user query
    embed_model = "text-embedding-ada-002"
    res = openai.Embedding.create(
        input=[question],
        engine=embed_model
    )

    # retrieve from Pinecone
    xq = res['data'][0]['embedding']
    res = index.query(xq, top_k=3, include_metadata=True)

    # get relevant information from Home Depot
    contexts = [item['metadata']['text'] for item in res['matches']]
    
    #to feed relevant information from Home Depot into the model and to append to appropriate channel history
    if source == "message":
        augmented_query = dmHistory + "\n\n---\n\n".join(contexts)+"\n\n-----\n\n"+question
    elif source == "channel":
        augmented_query = channelHistory + "\n\n---\n\n".join(contexts)+"\n\n-----\n\n"+question

    # system message to 'prime' the model
    primer = f"""You are Q&A bot. You are given input in the following order - chat history, 
    information provided by Home Depot, and then the user question. You are a highly intelligent system that answers
    user questions intelligently based on the. If the information can not be found in the information
    provided by the user you truthfully say "I don't know". Refrain from saying "based on the
    information". Whenver a user questions asks for links, only provide links to those products that you will mention
    in your response or have mentioned in the chat history - don't give extra links for extra products you did not mention. 
    """
    #generating response from model based on user query, Home Depot information, and conversation history
    res = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": primer},
            {"role": "user", "content": augmented_query}
        ]
    )
    #appending the user's query and model's response to the conversation hisory
    if source == "message":
        dmHistory += question + "\n" + res['choices'][0]['message']['content'] + "\n"
    elif source == "channel":
        channelHistory += question + "\n" + res['choices'][0]['message']['content'] + "\n"
    return res['choices'][0]['message']['content']

#direct messages
@app.event("message")
def handle_direct_message(event, say):
    if event.get("subtype") is None and event.get("channel_type") == "im":
        user_input = event["text"]
        if user_input == "clear":
            say("Clearing chat hisory...")
        else:
            say("Give me a few seconds...")
        #passing in user query into the model
        result = queryModel(user_input, "message")
        say(result)

#within channel
@app.event("app_mention")
def handle_mentions(body, say):
    user_input = body["event"]["text"]
    user_input = user_input.replace(os.environ["SLACK_BOT_USER_ID"], "").replace("<@>", "").strip()
    print(user_input)
    if user_input == "clear":
        say("Clearing conversation history...")
    else:
        say("Give me a few seconds...")
    #passing in user query into the model
    result = queryModel(user_input, "channel")
    say(result)


@flask_app.route("/slack/events", methods=["POST"])
def slack_events():
    """
    Route for handling Slack events.
    This function passes the incoming HTTP request to the SlackRequestHandler for processing.
    Returns:
        Response: The result of handling the request.
    """
    return handler.handle(request)


# Run the Flask app
if __name__ == "__main__":
    flask_app.run(port=3000)
