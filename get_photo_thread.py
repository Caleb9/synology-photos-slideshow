import PIL.ImageTk
import threading
import typing

import image_processor
import slideshow


class GetPhotoThread(threading.Thread):
    def __init__(self,
                 slideshow: slideshow.Slideshow,
                 image_processor: image_processor.ImageProcessor):
        super(GetPhotoThread, self).__init__(daemon=True)
        self._slideshow = slideshow
        self._image_processor = image_processor
        self.photo_image: typing.Optional[PIL.ImageTk.PhotoImage] = None
        self.error: typing.Optional[Exception] = None

    def run(self) -> None:
        try:
            image_bytes = self._slideshow.get_next_photo()
            self.photo_image = self._image_processor.bytes_to_photo_image(image_bytes)
        except Exception as error:
            self.photo_image = None
            self.error = error

    def is_failed(self) -> bool:
        return self.error is not None

    @staticmethod
    def start_get_next_photo_thread(slideshow: slideshow.Slideshow,
                                    image_processor: image_processor.ImageProcessor) -> "GetPhotoThread":
        result_thread = GetPhotoThread(slideshow, image_processor)
        result_thread.start()
        return result_thread
