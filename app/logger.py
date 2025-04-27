# app/logger.py 
# Yeah i know its not important, but i like it
import logging

logger = logging.getLogger("habit-tracker")
logger.setLevel(logging.DEBUG)

file_handler = logging.FileHandler("debug.log")
file_handler.setLevel(logging.DEBUG)

formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
file_handler.setFormatter(formatter)


if not logger.hasHandlers():
    logger.addHandler(file_handler)

stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.DEBUG)
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)