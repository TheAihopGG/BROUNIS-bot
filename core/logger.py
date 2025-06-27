import logging

logger = logging.getLogger(__name__)
logging.basicConfig(
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(
            filename="./logs.log",
            mode="w",
        ),
    ],
)
