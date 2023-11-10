module OpenAI
  class Speech
    def initialize(client:)
      @client = client
    end

    def create(parameters: {})
      @client.json_post(path: "/audio/speech", parameters: parameters)
    end
  end
end
