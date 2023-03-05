#!/usr/bin/env python3

import argparse
import datetime
from random import randrange
import sys
import tkinter.ttk
import typing

import PIL.ImageTk
import httpx

import get_photo_thread
import image_processor
import slideshow
import synology_photos_client


class App(tkinter.Tk):
    _MONITOR_LOOP_INTERVAL = 500

    def __init__(
            self,
            photos_client: synology_photos_client.PhotosClient,
            photo_change_interval_in_seconds: float,
            datetime_now: typing.Callable[[], datetime.datetime],
            randrange_: typing.Callable[[int, int], int]):
        super(App, self).__init__()
        self.attributes("-fullscreen", True)

        self._photos_client = photos_client
        self._photo_change_interval = datetime.timedelta(seconds=photo_change_interval_in_seconds)
        self._datetime_now = datetime_now
        self._randrange = randrange_

        self._slideshow: slideshow.Slideshow = None
        self._image_processor = image_processor.ImageProcessor((self.winfo_screenwidth(), self.winfo_screenheight()))
        self._label = tkinter.ttk.Label(self, background="black")
        self._label.pack(side="bottom", fill="both", expand=1)
        # For displaying errors
        self._label["foreground"] = "white"
        self._photo: typing.Optional[PIL.ImageTk.PhotoImage] = None

    def start_slideshow(self, start_from_random_photo: bool) -> "App":
        initial_album_offset = 0
        if start_from_random_photo:
            try:
                item_count = self._photos_client.get_album_contents_count()
                initial_album_offset = self._randrange(0, item_count)
            except Exception as error:
                eprint(f"[{self._datetime_now()}] Error (cannot start from random photo): {error}")
        self._slideshow = slideshow.Slideshow(self._photos_client, initial_album_offset)

        self._monitor(datetime.datetime.min,
                      self._start_get_next_photo_thread())
        return self

    def _monitor(
            self,
            last_photo_change: datetime.datetime,
            thread: get_photo_thread.GetPhotoThread) -> None:
        def schedule_next_iteration() -> None:
            self.after(self._MONITOR_LOOP_INTERVAL,
                       lambda: self._monitor(last_photo_change, thread))

        if thread.is_alive():
            # Next photo is still being downloaded or converted to PhotoImage
            schedule_next_iteration()
            return

        if thread.is_failed():
            # Getting next photo failed
            self._show_error(thread.error)
            # Retry after regular photo change interval (here expressed in milliseconds)
            self.after(
                self._photo_change_interval.seconds * 1000,
                lambda: self._monitor(self._datetime_now(), self._start_get_next_photo_thread()))
            return

        if self._datetime_now() - last_photo_change < self._photo_change_interval:
            # Current photo is still being displayed. Wait for another 500 ms.
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
        eprint(f"[{self._datetime_now()}] {error}")
        self._label["image"] = b""
        self._label["anchor"] = "center"
        self._label["text"] = str(error)


def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)
        

def parse_arguments(argv: [str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="synology-photos-slideshow.pex",
                                     description="Synology Photos album slideshow",
                                     epilog="Find new versions and more information on "
                                            "https://github.com/Caleb9/synology-photos-slideshow")
    parser.add_argument("share_link",
                        help="Link to a publicly shared album on Synology Photos. "
                             "Note that the album's privacy settings must be set to Public "
                             "and link password protection must be disabled.")

    def valid_interval(x) -> float:
        try:
            if float(x) < 1:
                raise argparse.ArgumentTypeError("%s is not greater or equal to 1" % x)
            return float(x)
        except ValueError:
            raise argparse.ArgumentTypeError("%s is not a number" % x)

    parser.add_argument("-i",
                        "--interval",
                        help="Photo change interval in seconds. Must be greater or equal to 1. "
                             "If not specified photos will change every 20 seconds",
                        type=valid_interval,
                        default=20)
    parser.add_argument("--random-start",
                        help="Initialize slideshow at randomly selected photo",
                        action="store_true")
    return parser.parse_args(argv)


def main(argv: [str]) -> None:
    args = parse_arguments(argv)

    with httpx.Client(timeout=20) as http_client:
        photos_client = synology_photos_client.PhotosClient(http_client,
                                                            args.share_link)
        App(photos_client,
            args.interval,
            datetime.datetime.now,
            randrange) \
            .start_slideshow(args.random_start) \
            .mainloop()


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    main(sys.argv[1:])
