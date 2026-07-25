from pages.base_page import BasePage


class AiChatPage(BasePage):
    INPUT_FIELD = "ai_chat_input_field"
    SEND_BUTTON = "ai_chat_send_button"

    def send_message(self, text: str):
        self.type_text(self.by_key(self.INPUT_FIELD), text)
        self.tap(self.by_key(self.SEND_BUTTON))
        self.wait(1.5)
