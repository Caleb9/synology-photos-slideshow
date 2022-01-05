def find_part_that_can_fit_to_window(
        window_size: (int, int),
        image_size: (int, int)) -> (float, float, float, float):
    window_x, window_y = window_size
    image_x, image_y = image_size
    factor_x = image_x / window_x
    factor_y = image_y / window_y
    factor = min(factor_x, factor_y)

    image_center_x = image_x / 2
    image_center_y = image_y / 2

    crop_x = window_x * factor
    crop_y = window_y * factor

    return \
        image_center_x - crop_x / 2, \
        image_center_y - crop_y / 2, \
        image_center_x + crop_x / 2, \
        image_center_y + crop_y / 2


def zoom(
        window_size: (int, int),
        image_size: (int, int)) -> (int, int):
    factor = max(__factor(window_size, image_size))
    image_x, image_y = image_size
    return int(image_x * factor), int(image_y * factor)


def scale(
        window_size: (int, int),
        image_size: (int, int)) -> (int, int):
    factor = min(__factor(window_size, image_size))
    image_x, image_y = image_size
    return int(image_x * factor), int(image_y * factor)


def center_box(
        window_size: (int, int),
        image_size: (int, int)) -> (int, int, int, int):
    window_x, window_y = window_size
    image_x, image_y = image_size
    window_center_x, window_center_y = window_x / 2, window_y / 2
    image_center_x, image_center_y = image_x / 2, image_y / 2
    return \
        int(window_center_x - image_center_x), \
        int(window_center_y - image_center_y), \
        int(window_center_x + image_center_x), \
        int(window_center_y + image_center_y)


def __factor(
        window_size: (int, int),
        image_size: (int, int)) -> (int, int):
    window_x, window_y = window_size
    image_x, image_y = image_size
    factor_x = window_x / image_x
    factor_y = window_y / image_y
    return factor_x, factor_y
