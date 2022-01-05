import unittest

import coordinate_calculator as sut


class CoordinateCalculatorTests(unittest.TestCase):
    def test_vertical_image(self):
        screen_size = 3840, 2160
        image_size = 1000, 1500

        x0, y0, x1, y1 = sut.find_part_that_can_fit_to_window(screen_size, image_size)

        expected = (0, 468, 1000, 1031)
        self.assertEqual(
            (int(x0), int(y0), int(x1), int(y1)),
            expected)

    def test_horizontal_image(self):
        screen_size = 3840, 2160
        image_size = 1500, 1000

        x0, y0, x1, y1 = sut.find_part_that_can_fit_to_window(screen_size, image_size)

        expected = (0, 78, 1500, 921)
        self.assertEqual(
            (int(x0), int(y0), int(x1), int(y1)),
            expected)


if __name__ == '__main__':
    unittest.main()
