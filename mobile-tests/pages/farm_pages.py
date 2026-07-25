from pages.base_page import BasePage


class FarmSetupPage(BasePage):
    NAME_FIELD = "farm_setup_name_field"
    AREA_FIELD = "farm_setup_area_field"
    CROP_FIELD = "farm_setup_crop_field"
    SOIL_FIELD = "farm_setup_soil_field"
    GPS_BUTTON = "farm_setup_gps_button"
    SUBMIT_BUTTON = "farm_setup_submit_button"

    def fill(self, name="", area="", crop="", soil=""):
        if name:
            self.type_text(self.by_key(self.NAME_FIELD), name)
        if area:
            self.type_text(self.by_key(self.AREA_FIELD), area)
        if crop:
            self.type_text(self.by_key(self.CROP_FIELD), crop)
        if soil:
            self.type_text(self.by_key(self.SOIL_FIELD), soil)

    def use_gps(self):
        self.tap(self.by_key(self.GPS_BUTTON))

    def submit(self):
        self.tap(self.by_key(self.SUBMIT_BUTTON))
        self.wait(2)


class FarmDataInputPage(BasePage):
    FARM_DROPDOWN = "farm_data_farm_dropdown"
    CROP_FIELD = "farm_data_crop_field"
    YIELD_FIELD = "farm_data_yield_field"
    FERTILIZER_FIELD = "farm_data_fertilizer_field"
    SHC_FIELD = "farm_data_shc_field"
    SAVE_BUTTON = "farm_data_save_button"

    def fill_crop_history(self, crop="", yield_kg="", fertilizer=""):
        if crop:
            self.type_text(self.by_key(self.CROP_FIELD), crop)
        if yield_kg:
            self.type_text(self.by_key(self.YIELD_FIELD), yield_kg)
        if fertilizer:
            self.type_text(self.by_key(self.FERTILIZER_FIELD), fertilizer)

    def fill_soil_health(self, shc_id=""):
        if shc_id:
            self.type_text(self.by_key(self.SHC_FIELD), shc_id)

    def save(self):
        self.tap(self.by_key(self.SAVE_BUTTON))
        self.wait(2)


class SensorsPage(BasePage):
    DEVICE_ID_FIELD = "sensors_device_id_field"
    PAIR_BUTTON = "sensors_pair_button"

    def pair_sensor(self, device_id: str):
        self.type_text(self.by_key(self.DEVICE_ID_FIELD), device_id)
        self.tap(self.by_key(self.PAIR_BUTTON))
        self.wait(1.5)
