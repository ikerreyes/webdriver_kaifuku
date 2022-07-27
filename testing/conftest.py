import contextlib
import subprocess
from urllib.request import urlopen

import pytest
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from wait_for import wait_for

BROWSER_IMAGE = "quay.io/redhatqe/selenium-standalone:latest"

_CHROME_OPTIONS = ChromeOptions()
_CHROME_OPTIONS.set_capability("acceptInsecureCerts", True)
_CHROME_OPTIONS.add_argument("--disable-application-cache")


CONFIGS = [
    pytest.param(
        {
            "expected_browser_name": "firefox",
            "webdriver": "Remote",
            "proxy_url": "http://example.com:8080",
            "webdriver_options": {
                "command_executor": "http://127.0.0.1:4444",
                "desired_capabilities": {
                    "browserName": "firefox",
                    "acceptInsecureCerts": True,
                },
            },
        },
        id="remote-firefox",
    ),
    pytest.param(
        {
            "expected_browser_name": "chrome",
            "webdriver": "Remote",
            "proxy_url": "http://example.com:8080",
            "webdriver_options": {
                "command_executor": "http://127.0.0.1:4444",
                "desired_capabilities": {
                    "browserName": "chrome",
                    "acceptInsecureCerts": True,
                    "chromeOptions": {
                        "args": ["--disable-application-cache"],
                    },
                    "goog:loggingPrefs": {"browser": "INFO", "performance": "ALL"},
                },
            },
        },
        id="remote-chrome",
    ),
    pytest.param(
        {
            "expected_browser_name": "firefox",
            "webdriver": "Remote",
            "proxy_url": "http://example.com:8080",
            "webdriver_options": {
                "command_executor": "http://127.0.0.1:4444",
                "options": FirefoxOptions(),
            },
        },
        id="remote-firefox-options",
    ),
    pytest.param(
        {
            "expected_browser_name": "chrome",
            "webdriver": "Remote",
            "proxy_url": "http://example.com:8080",
            "webdriver_options": {
                "command_executor": "http://127.0.0.1:4444",
                "options": _CHROME_OPTIONS,
                "desired_capabilities": {
                    "browserName": "chrome",
                    "goog:loggingPrefs": {"browser": "INFO", "performance": "ALL"},
                },
            },
        },
        id="remote-chrome-options",
    ),
]


@pytest.fixture(scope="session")
def selenium_container():
    ps = subprocess.run(
        [
            "podman",
            "run",
            "--rm",
            "-d",
            "-p",
            "127.0.0.1:4444:4444",
            "--shm-size=2g",
            BROWSER_IMAGE,
        ],
        capture_output=True,
    )
    wait_for(lambda: urlopen("http://127.0.0.1:4444"), timeout=180, handle_exception=True)
    container_id = ps.stdout.decode("utf-8").strip()
    yield container_id
    subprocess.run(["podman", "kill", container_id], stdout=subprocess.DEVNULL)


@pytest.fixture(params=CONFIGS)
def test_data(selenium_container, request: pytest.FixtureRequest):
    from webdriver_kaifuku import BrowserManager, log

    parameters = request.param  # type: ignore
    browser_name = parameters.pop("expected_browser_name")

    mgr = BrowserManager.from_conf(parameters)  # type: ignore
    log.warning(mgr)
    with contextlib.closing(mgr) as mgr:
        yield mgr, browser_name

    parameters["expected_browser_name"] = browser_name
