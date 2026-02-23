import logging

from loguru import logger


def configure_logging(level: str = "info") -> None:
    logging.basicConfig(level=getattr(logging, level.upper(), logging.INFO))
    logger.remove()
    logger.add(
        sink=lambda msg: logging.getLogger("sonicaid").log(
            logging.INFO, msg.rstrip("\n")
        ),
    )

