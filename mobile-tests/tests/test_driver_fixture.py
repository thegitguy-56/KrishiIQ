import pytest
from selenium.webdriver.remote.remote_connection import RemoteConnection

import conftest


@pytest.fixture(autouse=True)
def _restart_app_between_tests():
    yield


def test_driver_fixture_sets_webdriver_http_timeout(monkeypatch):
    class FakeOptions:
        def load_capabilities(self, caps):
            return {"caps": caps}

    class FakeSession:
        session_id = "fake-session-id"

        def __init__(self):
            self.implicit_wait_value = None
            self.quit_called = False

        def implicitly_wait(self, value):
            self.implicit_wait_value = value

        def quit(self):
            self.quit_called = True

    fake_session = FakeSession()
    call_args = {}

    def fake_remote(url, options):
        call_args["url"] = url
        call_args["options"] = options
        return fake_session

    monkeypatch.setattr(conftest, "UiAutomator2Options", FakeOptions)
    monkeypatch.setattr(conftest, "build_capabilities", lambda: {"appium:newCommandTimeout": 120})
    monkeypatch.setattr(conftest.webdriver, "Remote", fake_remote)
    monkeypatch.setattr(conftest.settings, "WEBDRIVER_HTTP_TIMEOUT", 17)
    monkeypatch.setattr(conftest.settings, "APPIUM_SERVER_URL", "http://127.0.0.1:4723/wd/hub")
    monkeypatch.setattr(conftest.settings, "IMPLICIT_WAIT", 10)

    RemoteConnection.set_timeout(1)
    fixture_gen = conftest.driver.__wrapped__()
    yielded = next(fixture_gen)

    assert yielded is fake_session
    assert RemoteConnection.get_timeout() == 17
    assert call_args["url"] == "http://127.0.0.1:4723/wd/hub"
    assert call_args["options"] == {"caps": {"appium:newCommandTimeout": 120}}
    assert fake_session.implicit_wait_value == 10

    with pytest.raises(StopIteration):
        next(fixture_gen)
    assert fake_session.quit_called is True
