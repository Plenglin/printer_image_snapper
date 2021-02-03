#!/usr/bin/env python3

import os

import requests
import structlog

logger = structlog.get_logger(__name__)

SNAPSHOT_URL = os.environ["SNAPSHOT_URL"]
PRINTER_ENDPOINT = os.environ["PRINTER_ENDPOINT"]
USER = os.environ["USER"]
PASSWORD = os.environ["PASSWORD"]


def main():
    logger.info("Fetching snapshot", url=SNAPSHOT_URL)
    snapshot = requests.get(SNAPSHOT_URL).content

    logger.info("PATCHing server image", url=PRINTER_ENDPOINT, username=USER, bytes=len(snapshot))
    response = requests.patch(PRINTER_ENDPOINT, auth=(USER, PASSWORD),
                              files={'image': ('snapshot.jpg', snapshot, 'image/jpg')})

    if response.status_code == 200:
        logger.info("Successfully uploaded snapshot", content=response.json())
    else:
        logger.error("Failed to upload snapshot", status_code=response.status_code, content=response.json())


if __name__ == '__main__':
    main()
