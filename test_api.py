import time
from random import randint

import requests
from loguru import logger

API_BASE_URL = ""
API_KEY = ""


def test_get_shortened_url(key: str) -> str:
    api_url = f"{API_BASE_URL}/{key}"

    logger.info(f"Getting shortened URL for key: {key}")
    logger.debug(f"GET {api_url}")

    response = requests.get(
        api_url,
        headers={"x-api-key": API_KEY},  # we need to pass the API key
        allow_redirects=False  # we don't want to follow the redirect
    )

    logger.debug(f"Response Status Code: {response.status_code}")
    assert response.status_code == 301

    logger.info(f"Redirect Location: {response.headers['Location']}")
    return response.headers["Location"]


def test_get_all_shortened_urls() -> int:
    api_url = f"{API_BASE_URL}/shortened-urls"

    logger.info(f"Getting all shortened URLs created with API Key: {API_KEY}")
    logger.debug(f"GET {api_url}")

    response = requests.get(
        api_url,
        headers={"x-api-key": API_KEY},  # we need to pass the API key
        allow_redirects=False  # we don't want to follow the redirect
    )

    logger.debug(f"Response Status Code: {response.status_code}")
    assert response.status_code == 200

    logger.info(f"Number of shortened URLs: {len(response.json())}")
    return len(response.json())


def test_create_shortened_url(key: str, url: str) -> str:
    api_url = f"{API_BASE_URL}/shortened-urls"

    logger.info(f"Creating shortened URL for key: {key} with URL: {url}")
    logger.debug(f"POST {api_url}")

    response = requests.post(
        api_url,
        headers={"x-api-key": API_KEY},  # we need to pass the API key
        json={
            "shortId": key,
            "url": url},
    )

    logger.debug(f"Response Status Code: {response.status_code}")
    assert response.status_code == 200
    assert response.json()["url"] == url

    logger.info(f"Shortened URL: {API_BASE_URL}/{key}")
    return api_url


def test_create_existing_url():
    random_string = f"test-url-{randint(0, 1000000)}"

    logger.info(f"Creating random shortened URL for key: {random_string}")

    test_create_shortened_url(random_string, "https://www.google.com")
    time.sleep(1)

    try:
        test_create_shortened_url(random_string, "https://www.google.com")
        assert False
    except AssertionError:
        assert True
    time.sleep(1)

    # delete the shortened url
    test_delete_shortened_url(random_string)


def test_delete_shortened_url(key: str):
    api_url = f"{API_BASE_URL}/{key}"

    logger.info(f"Deleting shortened URL for key: {key}")
    logger.debug(f"DELETE {api_url}")

    response = requests.delete(
        api_url,
        headers={"x-api-key": API_KEY},  # we need to pass the API key
    )

    logger.debug(f"Response Status Code: {response.status_code}")
    assert response.status_code == 200

    logger.info(f"Removed shortened URL: {api_url}")
    return key


if __name__ == "__main__":
    key = "backend"
    url = "https://github.com/hdm-reibe/ws23-0-backend"

    # we add sleep time to avoid throttling

    test_create_shortened_url(key, url)
    time.sleep(1)

    quit()
    test_get_all_shortened_urls()
    time.sleep(1)

    test_get_shortened_url(key)
    time.sleep(1)

    test_delete_shortened_url(key)
    time.sleep(1)

    test_create_existing_url()
