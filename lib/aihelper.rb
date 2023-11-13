require 'json'
require_relative 'openai'
require 'rest-client'

OpenAI.configure do |config|
  config.access_token = 'OPENAI_KEY_REDACTED'
  config.organization_id = 'org-AQP4h0lMfOWuCW9WabhnxRRl'
end

client = OpenAI::Client.new

# puts client.models.list['data'].map{|data| data['id'] }

# client.chat(
#     parameters: {
#         model: "gpt-3.5-turbo", # Required.
#         messages: [{ role: "user", content: "Напиши хоку"}], # Required.
#         temperature: 0.7,
#         stream: proc do |chunk, _bytesize|
#             print chunk.dig("choices", 0, "delta", "content")
#         end
#     })

client.chat(
    parameters: {
        model: "gpt-4", # Required.
        messages: [{ role: "user", content: <<-EOF

        
        EOF
        }], # Required.
        temperature: 0.9,
        stream: proc do |chunk, _bytesize|
            print chunk.dig("choices", 0, "delta", "content")
        end
    })

# response = client.images.generate(parameters: { prompt: "Сделай иллюстрацию к новости: Официальный представитель МИД РФ Мария Захарова заявила в своем Telegram-канале, что в списках на эвакуацию из сектора Газа числится очень много детей.
# Как передавало ИА Регнум, Египет 1 ноября открыл терминал КПП «Рафах» на границе с сектором Газа, чтобы впустить около 90 раненых палестинцев и около 450 иностранцев.
# Девятого ноября Захарова сказала, что в МИД РФ шокированы заявлением посла Израиля о сроках эвакуации россиян из Газы.
# 8 ноября посол Израиля в Москве Александр Бен Цви заявил, что согласование эвакуации граждан РФ из сектора Газа может занять до двух недель.", size: "1024x1024" })
# puts response.dig("data", 0, "url")
# => "https://oaidalleapiprodscus.blob.core.windows.net/private/org-Rf437IxKhh..."

# OpenAI.rough_token_count("Your text")

# response = client.chat(
#     parameters: {
#         model: "gpt-3.5-turbo", # Required.
#         messages: [{ role: "user", content: "Say this is a test!"}], # Required.
#         temperature: 0.7,
#     })
# puts response.dig("choices", 0, "message", "content")

# response = client.audio.translate(
#     parameters: {
#         model: "whisper-1",
#         file: File.open("./tiroler.m4a", "rb"),
#         # language: 'ru',
#     })
# puts response["text"]

# response = client.audio.transcribe(
#     parameters: {
#         model: "whisper-1",
#         file: File.open("./tiroler.m4a", "rb"),
#     })
# puts response["text"]

# response = client.speech.create(
#     parameters: {
#         model: "tts-1",
#         input: 'Сегодня КЛАССНЫЙ день!, малыш я счастлива что ТЫ у меня есть!', # "Today is a wonderful day to build something people love!",
#         voice: "nova" # alloy, echo, fable, onyx, nova, and shimmer
#     })
# File.open('output.mp3', 'w') { |file| file.write(response) }


# client.chat(
#   parameters: {
#     model: "gpt-4-vision-preview", # Required.
#     messages: [{ role: "user", content: [
#       {
#         "type": "text",
#         "text": "What are in these images? Is there any difference between them?"
#       },
#       {
#         "type": "image_url",
#         "image_url": {
#           "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/dd/Gfp-wisconsin-madison-the-nature-boardwalk.jpg/2560px-Gfp-wisconsin-madison-the-nature-boardwalk.jpg",
#         }
#       },
#       {
#         "type": "image_url",
#         "image_url": {
#           "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/dd/Gfp-wisconsin-madison-the-nature-boardwalk.jpg/2560px-Gfp-wisconsin-madison-the-nature-boardwalk.jpg",
#         }
#       }
#     ]}],
#     temperature: 0.7,
#     stream: proc do |chunk, _bytesize|
#       print chunk.dig("choices", 0, "delta", "content")
#     end
#   }
# )


# # Example dummy function hard coded to return the same weather
# # In production, this could be your backend API or an external API
# def get_current_weather(location:, unit: "fahrenheit")
#   if location.downcase.include? "tokyo"
#     return {"location" => "Tokyo", "temperature" => "10", "unit" => "celsius"}
#   elsif location.downcase.include? "san francisco"
#     return {"location" => "San Francisco", "temperature" => "72", "unit" => "fahrenheit"}
#   elsif location.downcase.include? "paris"
#     return {"location" => "Paris", "temperature" => "22", "unit" => "celsius"}
#   else
#     return {"location" => location, "temperature" => "unknown"}
#   end
# end

# def run_conversation()
#   # Step 1: send the conversation and available functions to the model
#   messages = [{"role" => "user", "content" => "What's the weather like in San Francisco, Tokyo, and Paris?"}]
#   tools = [
#       {
#           "type" => "function",
#           "function" => {
#               "name" => "get_current_weather",
#               "description" => "Get the current weather in a given location",
#               "parameters" => {
#                   "type" => "object",
#                   "properties" => {
#                       "location" => {
#                           "type" => "string",
#                           "description" => "The city and state, e.g. San Francisco, CA",
#                       },
#                       "unit" => {"type" => "string", "enum" => ["celsius", "fahrenheit"]},
#                   },
#                   "required" => ["location"],
#               },
#           },
#       }
#   ]

#   client = OpenAI::Client.new
#   response = client.completion.create(parameters: {
#     model: "gpt-3.5-turbo-1106",
#     messages: messages,
#     tools: tools,
#     tool_choice: "auto"  # auto is default, but we'll be explicit
#   })
#   response_message = response.dig("choices", 0, "message")
#   tool_calls = response.dig("choices", 0, "message", "tool_calls")

#   # Step 2: check if the model wanted to call a function
#   if tool_calls
#     # Step 3: call the function
#     # Note: the JSON response may not always be valid; be sure to handle errors
#     available_functions = {
#         "get_current_weather" => method(:get_current_weather),
#     }
#     messages.append(response_message) # extend conversation with assistant's reply

#     # Step 4: send the info for each function call and function response to the model
#     tool_calls.each do |tool_call|
#       function_name = tool_call.dig("function", "name")
#       function_to_call = available_functions[function_name]
#       function_args = JSON.parse(tool_call.dig("function", "arguments"))
#       function_response = function_to_call.call(
#           location: function_args["location"],
#           unit: function_args["unit"],
#       )
#       messages.append(
#           {
#               "tool_call_id" => tool_call['id'],
#               "role" => "tool",
#               "name" => function_name,
#               "content" => function_response.to_json,
#           }
#       )
#     end

#     second_response = client.completion.create(parameters: {
#         model: "gpt-3.5-turbo-1106",
#         messages: messages,
#     })
#     return second_response
#   end
# end

# response = run_conversation()

# puts response.dig("choices", 0, "message", 'content') # => The current weather in San Francisco is 72°F, in Tokyo it is 10°C, and in Paris it is 22°C.



# сделать ассистента который выполняет код на python

