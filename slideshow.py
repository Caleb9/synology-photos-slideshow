import synology_photos_client


class Slideshow:
    def __init__(
            self,
            photos_client: synology_photos_client.PhotosClient):
        self._photos_client = photos_client
        self._album_offset = 0
        self._photos_batch: list[synology_photos_client.PhotosClient.PhotoDto] = []
        self._batch_photo_index = 0

    _PHOTOS_BATCH_SIZE = 10

    def get_next_photo(self) -> bytes:
        if self._slideshow_ended():
            self._album_offset = 0
        if self._need_next_batch():
            self._photos_batch = self._photos_client.get_album_contents(self._album_offset, self._PHOTOS_BATCH_SIZE)
            self._album_offset += self._PHOTOS_BATCH_SIZE
            self._batch_photo_index = 0

        if len(self._photos_batch) > 0:
            photo_dto = self._photos_batch[self._batch_photo_index]
            photo_bytes = self._photos_client.get_photo(photo_dto["id"], photo_dto["thumbnail"]["cache_key"])
            self._batch_photo_index += 1
            return photo_bytes

        return self.get_next_photo()

    def _slideshow_ended(self) -> bool:
        return len(self._photos_batch) < self._PHOTOS_BATCH_SIZE and self._need_next_batch()

    def _need_next_batch(self) -> bool:
        return self._batch_photo_index == len(self._photos_batch)
