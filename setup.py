# Needed by pex

from distutils.core import setup
setup(
    name="synology-photos-slideshow",
    version="0.0.0",
    py_modules=["coordinate_calculator", "slideshow", "synology_photos_client"],
    scripts=["main.py"],
)
