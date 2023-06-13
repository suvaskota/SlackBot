# SlackBot
I created a SlackBot for users to ask questions about Home Depot products. Here are some of the usage details:
- You chat with this SlackBot is two ways - direct message on the workspace or by mentioning the bot (@ProductAssistant) in the "general" channel and then stating your question. 
- The bot will keep the conversation history in memory so you can ask follow up questions as well. If you decide to move to a new topic please type in the message "clear" (in direct message) or "@ProductAssistant clear" in the general channel so that the Slackbot can free its memory to answer your questions more efficiencty and accurately. 
- The channel conversation memory and direct message memories are independent.
- If the query takes longer than ~30 seconds to get back to you, just try again because it means that the OpenAI is being overloaded with  requests in general from other external companies/applications/users

## Technology Stack
- OpenAI (gpt-3.5-turbo for chat completions & text-embedding-ada-002 for embedding)
- langchain
- Pincone Vector Database
- Python Flask
- Python Pandas for data cleaning & formatting
- Slack API


