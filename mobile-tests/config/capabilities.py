"""
Desired capabilities for the appium-flutter-driver session.

`automationName: Flutter` tells Appium to route through the
appium-flutter-driver plugin instead of UiAutomator2, which is required
because KrishiIQ is a Flutter app and most of its widgets are not exposed
as native Android views.
"""
from config.settings import settings


def build_capabilities() -> dict:
    return {
        "platformName": settings.PLATFORM_NAME,
        "appium:platformVersion": settings.PLATFORM_VERSION,
        "appium:deviceName": settings.DEVICE_NAME,
        "appium:automationName": settings.AUTOMATION_NAME,
        "appium:app": settings.APK_PATH,
        "appium:appPackage": settings.APP_PACKAGE,
        "appium:appActivity": settings.APP_ACTIVITY,
        "appium:newCommandTimeout": settings.NEW_COMMAND_TIMEOUT,
        "appium:autoGrantPermissions": True,
        "appium:noReset": False,
        "appium:fullReset": False,
    }
