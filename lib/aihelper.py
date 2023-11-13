from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# import os
# print(os.getenv("OPENAI_API_KEY"))  # should print your API key

client = OpenAI(
  # Defaults to os.environ.get("OPENAI_API_KEY")
  # Otherwise use: api_key="Your_API_Key",
)

# response = client.chat.completions.create(
#   model="gpt-3.5-turbo",
#   messages=[
#         {"role": "user", "content": "Напиши хоку"},
#     ],
#   temperature=0.7
# )
# print(response.choices[0].message.content)

##############################################

# import json

# # Example dummy function hard coded to return the same weather
# # In production, this could be your backend API or an external API
# def get_current_weather(location, unit="fahrenheit"):
#     """Get the current weather in a given location"""
#     if "tokyo" in location.lower():
#         return json.dumps({"location": location, "temperature": "10", "unit": "celsius"})
#     elif "san francisco" in location.lower():
#         return json.dumps({"location": location, "temperature": "72", "unit": "fahrenheit"})
#     else:
#         return json.dumps({"location": location, "temperature": "22", "unit": "celsius"})

# def run_conversation():
#   # Step 1: send the conversation and available functions to the model
#   messages = [{"role": "user", "content": "What's the weather like in San Francisco, Tokyo, and Paris?"}]
#   tools = [
#       {
#           "type": "function",
#           "function": {
#               "name": "get_current_weather",
#               "description": "Get the current weather in a given location",
#               "parameters": {
#                   "type": "object",
#                   "properties": {
#                       "location": {
#                           "type": "string",
#                           "description": "The city and state, e.g. San Francisco, CA",
#                       },
#                       "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]},
#                   },
#                   "required": ["location"],
#               },
#           },
#       }
#   ]
#   response = client.chat.completions.create(
#       model="gpt-4-1106-preview", # gpt-4-1106-preview
#       messages=messages,
#       tools=tools,
#       tool_choice="auto",  # auto is default, but we'll be explicit
#   )
#   response_message = response.choices[0].message
#   tool_calls = response_message.tool_calls
#   # Step 2: check if the model wanted to call a function
#   if tool_calls:
#       # Step 3: call the function
#       # Note: the JSON response may not always be valid; be sure to handle errors
#       available_functions = {
#           "get_current_weather": get_current_weather,
#       }  # only one function in this example, but you can have multiple
#       messages.append(response_message)  # extend conversation with assistant's reply
#       # Step 4: send the info for each function call and function response to the model
#       for tool_call in tool_calls:
#           function_name = tool_call.function.name
#           function_to_call = available_functions[function_name]
#           function_args = json.loads(tool_call.function.arguments)
#           function_response = function_to_call(
#               location=function_args.get("location"),
#               unit=function_args.get("unit"),
#           )
#           messages.append(
#               {
#                   "tool_call_id": tool_call.id,
#                   "role": "tool",
#                   "name": function_name,
#                   "content": function_response,
#               }
#           )  # extend conversation with function response
#       second_response = client.chat.completions.create(
#           model="gpt-4-1106-preview", # gpt-4-1106-preview
#           messages=messages,
#       )  # get a new response from the model where it can see the function response
#       return second_response

# response = run_conversation()
# print(response.choices[0].message.content)

##############################

# messages = [
#   {"role": "system", "content": "Ты полезный помощник"},
#   {"role": "user", "content": "Кто выиграл мировую серию в 2020?"},
#   {"role": "assistant", "content": "The Los Angeles Dodgers won the World Series in 2020."},
#   {"role": "user", "content": "Где играли?"}
# ]

# response = client.chat.completions.create(
#   model = "gpt-3.5-turbo-16k-0613",
#   messages = messages
# )

# print(response.choices[0].message.content)
# messages.append(response.choices[0].message)
# messages.append({"role": "user", "content": "Сколько набрали очков?"})
# print('Сколько набрали очков?')

# response = client.chat.completions.create(
#   model = "gpt-3.5-turbo-16k-0613",
#   messages = messages
# )

# print(response.choices[0].message.content)

# ############################################

# messages = [
#   {"role": "system", "content": "Ты полезный помощник"},
#   {"role": "user", "content": "Кто выиграл мировую серию в 2020?"},
#   {"role": "assistant", "content": "The Los Angeles Dodgers won the World Series in 2020."},
#   {"role": "user", "content": "Где играли?"}
# ]

# response = client.chat.completions.create(
#   model = "gpt-3.5-turbo-16k-0613",
#   messages = messages
#   stream = True
# )
# for chunk in response:
#   print(chunk.choices[0].delta.content, end = "")


############################## Assistant

assistant = client.beta.assistants.create(
  name="Math Tutor",
  instructions="You are a personal math tutor. Write and run code to answer math questions.",
  tools=[{"type": "code_interpreter"}],
  model="gpt-4-1106-preview"
)

thread = client.beta.threads.create()

message = client.beta.threads.messages.create(
  thread_id=thread.id,
  role="user",
  content="I need to solve the equation `3x + 11 = 14`. Can you help me?"
)

run = client.beta.threads.runs.create(
  thread_id=thread.id,
  assistant_id=assistant.id,
  instructions="Please address the user as Jane Doe. The user has a premium account."
)

run = client.beta.threads.runs.retrieve(
  thread_id=thread.id,
  run_id=run.id
)

# wait until run status='completed'

messages = client.beta.threads.messages.list(
  thread_id=thread.id
)

print(messages)
