module OpenAI
  class Completion
    def initialize(client:)
      @client = client
    end

    def create(parameters: {})
      @client.json_post(path: "/chat/completions", parameters: parameters)
    end
  end
end
