from pages.base_page import BasePage


class CropHealthPage(BasePage):
    FARM_DROPDOWN = "crop_health_farm_dropdown"
    IMAGE_PICKER_AREA = "crop_health_image_picker_area"
    DETECT_BUTTON = "crop_health_detect_button"

    def open_image_source_dialog(self):
        self.tap(self.by_key(self.IMAGE_PICKER_AREA))
        self.wait(1)

    def choose_camera(self):
        self.tap(self.by_text("Camera"))

    def choose_gallery(self):
        self.tap(self.by_text("Gallery"))

    def select_farm(self):
        self.tap(self.by_key(self.FARM_DROPDOWN))

    def tap_detect(self):
        self.tap(self.by_key(self.DETECT_BUTTON))
        self.wait(2)

    def upload_and_detect(self, source: str = "gallery"):
        self.open_image_source_dialog()
        if source == "camera":
            self.choose_camera()
        else:
            self.choose_gallery()
        self.wait(1)
        self.tap_detect()
