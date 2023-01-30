#!/usr/bin/env python3

import datetime
import sys
import tkinter.ttk
import typing

import httpx
import PIL.ImageTk

import image_processor
import get_photo_thread
import slideshow
import synology_photos_client


class App(tkinter.Tk):
    MONITOR_LOOP_INTERVAL = 100

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

        self._image_processor = image_processor.ImageProcessor((self.winfo_screenwidth(), self.winfo_screenheight()))
        self._label = tkinter.ttk.Label(self, background="black")
        self._label.pack(side="bottom", fill="both", expand=1)
        # For displaying errors
        self._label["foreground"] = "white"
        self._photo: typing.Optional[PIL.ImageTk.PhotoImage] = None

    def start_slideshow(self) -> "App":
        self._monitor(datetime.datetime.min,
                      self._start_get_next_photo_thread())
        return self

    def _monitor(
            self,
            last_photo_change: datetime.datetime,
            thread: get_photo_thread.GetPhotoThread) -> None:
        def schedule_next_iteration() -> None:
            self.after(self.MONITOR_LOOP_INTERVAL,
                       lambda: self._monitor(last_photo_change, thread))

        if thread.is_alive():
            # Next photo is still being downloaded or converted to PhotoImage
            schedule_next_iteration()
            return

        if thread.is_failed():
            # Getting next photo failed
            self._show_error(thread.error)
            print(f"[{self._datetime_now()}] {thread.error}")
            # Retry after regular photo change interval (here expressed in milliseconds)
            self.after(
                self._photo_change_interval.seconds * 1000,
                lambda: self._monitor(self._datetime_now(), self._start_get_next_photo_thread()))
            return

        if self._datetime_now() - last_photo_change < self._photo_change_interval:
            # Current photo is still being displayed. Wait for another 100 ms.
            schedule_next_iteration()
            return
        # Next photo is ready and current photo has been shown for required duration. Show next photo and start fetching
        # subsequent one in the background.
        self._show_image(thread.photo_image)
        last_photo_change = self._datetime_now()
        thread = self._start_get_next_photo_thread()
        schedule_next_iteration()

    def _start_get_next_photo_thread(self) -> get_photo_thread.GetPhotoThread:
        return get_photo_thread.GetPhotoThread.start_get_next_photo_thread(self._slideshow,
                                                                           self._image_processor)

    def _show_image(self, photo_image: PIL.ImageTk.PhotoImage) -> None:
        self._label["text"] = None
        # We need to hold a reference to PhotoImage, else it won't show up. See https://stackoverflow.com/a/15216402
        self._photo = photo_image
        self._label["image"] = self._photo

    def _show_error(self, error: Exception) -> None:
        self._label["image"] = b""
        self._label["anchor"] = "center"
        self._label["text"] = str(error)


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
