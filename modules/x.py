import time
from typing import Any, Dict

import requests

from modules.tweet_id_storage import TweetIdStorage
from settings import BEARER_TOKEN, MAX_RETRIES, PROXY


class XAPIHandler:
    BASE_URL = "https://api.x.com/2"

    def __init__(self):
        self.tweet_id_storage = TweetIdStorage()

    def _make_request(
        self,
        endpoint: str,
        method: str,
        data: Dict[str, Any] = {},
        params: Dict[str, str] = {},
    ) -> Dict[str, Any]:
        headers = {
            "Authorization": f"Bearer {BEARER_TOKEN}",
        }

        retries = 0
        while retries < MAX_RETRIES:
            try:
                response = requests.request(
                    method=method,
                    url=self.BASE_URL + endpoint,
                    headers=headers,
                    data=data,
                    params=params,
                    proxies={"http": PROXY, "https": PROXY}
                    if PROXY != "scheme://username:password@host:port"
                    else None,
                )
                response.raise_for_status()

                return response.json()
            except requests.exceptions.HTTPError as error:
                if error.response.status_code == 429:
                    reset_time = error.response.headers["X-Rate-Limit-Reset"]
                    time_to_wait = int(reset_time) - int(time.time())
                    print(
                        f"Превышено максимальное количество запросов. Подождите {time_to_wait} секунд"
                    )
                    time.sleep(time_to_wait)
                else:
                    print(error.response.text)
                    retries += 1

        raise Exception("Превышено максимальное количество попыток")

    def fetch_user_id_by_username(self, username: str) -> str:
        user = self._make_request(f"/users/by/username/{username}", method="GET")

        return user["data"]["id"]

    def fetch_user_tweets(self, username: str, user_id: str) -> Dict[str, Any]:
        last_tweet_id = self.tweet_id_storage.get_last_tweet_id(username)

        params = {
            "expansions": "attachments.media_keys,referenced_tweets.id",
            "media.fields": "url,type,media_key",
            "tweet.fields": "text,note_tweet",
        }

        if last_tweet_id:
            params["since_id"] = last_tweet_id
            params["max_results"] = "100"
        else:
            params["max_results"] = "5"

        return self._make_request(
            f"/users/{user_id}/tweets", method="GET", params=params
        )

    def get_tweet_by_id(self, tweet_id: str) -> Dict[str, Any]:
        params = {
            "expansions": "attachments.media_keys,referenced_tweets.id",
            "media.fields": "url,type,media_key",
            "tweet.fields": "text,note_tweet",
        }

        return self._make_request(f"/tweets/{tweet_id}", method="GET", params=params)
