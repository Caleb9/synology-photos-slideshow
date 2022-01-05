#!/usr/bin/env python3

import datetime
import io
import sys
import tkinter.ttk
import typing

import PIL.Image
import PIL.ImageFilter
import PIL.ImageTk
import httpx

import coordinate_calculator
import slideshow
import synology_photos_client


class App(tkinter.Tk):
    def __init__(
            self,
            slideshow_: slideshow.Slideshow,
            photo_change_interval_in_seconds: int,
            datetime_now: typing.Callable[[], datetime.datetime]):
        super(App, self).__init__()
        self.attributes("-fullscreen", True)

        self._slideshow = slideshow_
        self._photo_change_interval = datetime.timedelta(seconds=photo_change_interval_in_seconds)
        self._datetime_now = datetime_now

        self._label = tkinter.ttk.Label(self, background="black")
        self._label.pack(side="bottom", fill="both", expand=1)
        # For displaying errors
        self._label["foreground"] = "white"
        self._screen_size = self.winfo_screenwidth(), self.winfo_screenheight()
        self._photo = None

    MONITOR_LOOP_INTERVAL = 100

    def start_slideshow(self) -> "App":
        self._monitor(
            self._start_get_next_photo_thread(),
            datetime.datetime.min)
        return self

    def _start_get_next_photo_thread(self) -> slideshow.GetNextPhotoThread:
        return slideshow.GetNextPhotoThread.start_get_next_photo_thread(self._slideshow)

    def _monitor(
            self,
            thread: slideshow.GetNextPhotoThread,
            last_photo_change: datetime.datetime) -> None:
        def schedule_next_iteration() -> None:
            self.after(self.MONITOR_LOOP_INTERVAL, lambda: self._monitor(thread, last_photo_change))

        if thread.is_alive():
            # Next photo is still being downloaded
            schedule_next_iteration()
            return

        if thread.is_failed():
            # Getting next photo failed
            self._show_error(thread.error)
            print(f"[{self._datetime_now()}] {thread.error}")
            # Retry after regular photo change interval (here expressed in milliseconds)
            self.after(
                self._photo_change_interval.seconds * 1000,
                lambda: self._monitor(self._start_get_next_photo_thread(), self._datetime_now()))
            return

        # Current photo display time so far, corrected by monitor loop interval
        current_photo_display_time = \
            self._datetime_now() - last_photo_change + datetime.timedelta(milliseconds=self.MONITOR_LOOP_INTERVAL)
        if current_photo_display_time < self._photo_change_interval:
            # Current photo is still showing. Wait for another 100 ms.
            schedule_next_iteration()
            return
        # Next photo is ready and current photo has been shown for required duration. Show next photo and start fetching
        # subsequent one immediately.
        self._show_image(thread.image_bytes)
        last_photo_change = self._datetime_now()
        thread = self._start_get_next_photo_thread()
        schedule_next_iteration()

    def _show_image(self, image_bytes: bytes) -> None:
        self._label["text"] = None
        result = self._bytes_to_photo_image(image_bytes)
        if isinstance(result, Exception):
            self._show_error(result)
            return
        # We need to hold a reference to PhotoImage, else it won't show up. See https://stackoverflow.com/a/15216402
        self._photo = result
        self._label["image"] = self._photo

    def _show_error(self, error: Exception) -> None:
        self._label["image"] = b""
        self._label["anchor"] = "center"
        self._label["text"] = str(error)

    def _bytes_to_photo_image(
            self,
            image_bytes: bytes) -> typing.Union[PIL.ImageTk.PhotoImage, Exception]:
        screen_size = self._screen_size
        try:
            with PIL.Image.open(io.BytesIO(image_bytes)) as image:
                image_size = image.width, image.height
                cropped_part_coordinates = coordinate_calculator.find_part_that_can_fit_to_window(screen_size,
                                                                                                  image_size)
                cropped_width = cropped_part_coordinates[2] - cropped_part_coordinates[0]
                cropped_height = cropped_part_coordinates[3] - cropped_part_coordinates[1]
                zoomed_coordinates = coordinate_calculator.zoom(screen_size, (cropped_width, cropped_height))
                with image.crop(cropped_part_coordinates) as screen_part, \
                        screen_part.resize(zoomed_coordinates) as zoom, \
                        zoom.filter(PIL.ImageFilter.GaussianBlur(50)) as background, \
                        image.resize(coordinate_calculator.scale(screen_size, image_size)) as foreground:
                    background.putalpha(200)
                    background.paste(
                        foreground,
                        coordinate_calculator.center_box(screen_size, (foreground.width, foreground.height)))
                    return PIL.ImageTk.PhotoImage(background)
        except PIL.UnidentifiedImageError as error:
            return error


help_message = f"""Provide the following arguments:
    share_link  [REQUIRED] Link to a publicly shared album on Synology Photos.
                Note that the album's privacy settings must be set to Public
                and link password protection must be disabled. 
    interval    [OPTIONAL] Photo change interval in seconds.
                Must be a positive number.
                If not specified photos will change every 20 seconds

Example:
    {sys.argv[0]} https://my.nas/is/sharing/ABcd1234Z 30
"""


def main(argv: [str]) -> None:
    if len(argv) < 1:
        print(help_message)
        sys.exit(1)
    share_link = argv[0]
    photo_change_interval_in_seconds = 20
    if len(argv) > 1:
        photo_change_interval_in_seconds = int(argv[1])
        if photo_change_interval_in_seconds < 1:
            print("Invalid interval value. Must be a positive number")
            sys.exit(2)

    with httpx.Client(timeout=20) as http_client:
        App(
            slideshow.Slideshow(
                synology_photos_client.PhotosClient(
                    http_client,
                    share_link)),
            photo_change_interval_in_seconds,
            datetime.datetime.now) \
            .start_slideshow() \
            .mainloop()


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    main(sys.argv[1:])
