import logging
import sys

# get logger
logger = logging.getLogger()

# create formatter
formatter = logging.Formatter(fmt="%(asctime)s - %(levelname)s - %(message)s")

# create handlers
stream_handler = logging.StreamHandler(sys.stdout)

"""
remove filehandler for serverless hosting to prevent issues This error occurs because Vercel's serverless environment has a read-only filesystem,
and your code is trying to write to a file (app.log) using logging.FileHandler
file_handler = logging.FileHandler('app.log')
file_handler.setFormatter(formatter)
logger.handlers = [stream_handler, file_handler]
"""
stream_handler.setFormatter(formatter)

# add handlers to the logger
logger.handlers = [stream_handler]


# set log level
logger.setLevel(logging.INFO)
