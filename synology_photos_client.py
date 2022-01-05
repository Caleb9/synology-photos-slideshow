import typing

import httpx


class PhotosClient:
    def __init__(
            self,
            http_client: httpx.Client,
            share_link: str):
        self._http_client = http_client
        self._share_link = share_link
        last_separator_index = share_link.rfind("/")
        self._api_url = share_link[:last_separator_index] + "/webapi/entry.cgi/"
        self._passphrase = share_link[last_separator_index + 1:]
        self._sharing_sid = ""

    class Thumbnail(typing.TypedDict):
        xl: str
        cache_key: str

    class PhotoDto(typing.TypedDict):
        id: int
        thumbnail: "PhotosClient.Thumbnail"

    def get_album_contents(self, offset: int, limit: int) -> list[PhotoDto]:
        self._get_sharing_sid_cookie()

        data = {
            "api": "SYNO.Foto.Browse.Item",
            "method": "list",
            "version": 1,
            "additional": "[\"thumbnail\"]",
            "offset": offset,
            "limit": limit,
            "sort_by": "takentime",
            "sort_direction": "asc"
        }
        response = self._http_client.post(self._api_url,
                                          data=data,
                                          headers=[("X-SYNO-SHARING", self._passphrase)])
        response_content = response.json()
        if not response_content["success"]:
            raise Exception(f"Listing album contents resulted with API error {response_content['error']}")
        return [{"id": photo_dto["id"], "thumbnail": photo_dto["additional"]["thumbnail"]}
                for photo_dto in response_content["data"]["list"]]

    def get_photo(self, photo_id: int, cache_key: str) -> bytes:
        self._get_sharing_sid_cookie()

        params = {
            "api": "SYNO.Foto.Thumbnail",
            "method": "get",
            "version": 2,
            "_sharing_id": self._passphrase,
            "id": photo_id,
            "cache_key": cache_key,
            "type": "unit",
            "size": "xl",
        }
        response = self._get(self._api_url, params)
        return response.read()

    def _get_sharing_sid_cookie(self) -> None:
        if "sharing_sid" in self._http_client.cookies.keys():
            return

        data = {
            "api": "SYNO.Core.Sharing.Login",
            "method": "login",
            "version": 1,
            "sharing_id": self._passphrase
        }
        response = self._http_client.post(self._api_url, data=data)
        response_content = response.json()
        if not response_content["success"]:
            raise Exception(f"Obtaining sharing_sid cookie resulted with API error {response_content['error']}")

    def _get(self, url: str, params: typing.Optional[dict] = None) -> httpx.Response:
        response = self._http_client.get(url, params=params)
        if response.status_code == 200:
            return response
        raise Exception(
            f"{url} responded with status {response.status_code}: {response.reason_phrase}")
