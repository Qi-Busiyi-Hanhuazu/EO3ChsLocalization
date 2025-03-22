from helper import (
  DIR_IMAGES,
  DIR_IMAGES_REPLACE_ADDITIONAL,
  DIR_REPACK_DATA,
  DIR_UNAPCKED_DATA,
)
from import_images import import_images

if __name__ == "__main__":
  import_images(f"{DIR_UNAPCKED_DATA}/{DIR_IMAGES}", DIR_IMAGES_REPLACE_ADDITIONAL, f"{DIR_REPACK_DATA}/{DIR_IMAGES}")
