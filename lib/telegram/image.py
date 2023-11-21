class Image:
    def __init__(self, openai):
        self.openai = openai

    def generate(self, image_description):
        try:
            response = self.openai.images.generate(
                prompt=image_description,
                model="dall-e-3",
                quality="standard",
                n=1,
                size="1024x1024"
            )
            print(response)
            # Check if the response has the expected attributes
            if hasattr(response, 'data') and response.data:
                return response.data[0].url  # Accessing URL using proper object notation
            else:
                return "No image generated"
        except Exception as e:
            return f"Error in generating image: {e}"
