import io

import PIL.Image
import PIL.ImageFilter
import PIL.ImageTk

import coordinate_calculator


class ImageProcessor:
    def __init__(self, screen_size: tuple[int, int]):
        self._screen_size = screen_size

    def bytes_to_photo_image(
            self,
            image_bytes: bytes) -> PIL.ImageTk.PhotoImage:
        screen_size = self._screen_size
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
