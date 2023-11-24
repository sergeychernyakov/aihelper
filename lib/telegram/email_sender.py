class EmailSender:
    def __init__(self, openai):
        self.openai = openai

    def send_email(self, email, text, attachment = None):
        print(f'Sendind email: image with description: "{image_description}"')
        # try:
        #     # send email here
        # except Exception as e:
        #     return f"Error in generating image: {e}",''

# Example of usage:
