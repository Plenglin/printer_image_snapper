#!/usr/bin/env python3
import os
import sys

import requests
import structlog
from requests import RequestException

logger = structlog.get_logger(__name__)

SNAPSHOT_URL = os.getenv("SNAPSHOT_URL")
OCTOPRINT_KEY = os.getenv("OCTOPRINT_KEY")
OCTOPRINT_ROOT = os.getenv("OCTOPRINT_ROOT")
PRINTER_ENDPOINT = os.getenv("PRINTER_ENDPOINT")
USER = os.getenv("USER")
PASSWORD = os.getenv("PASSWORD")


def get_printer_status():
    headers = {'X-Api-Key': OCTOPRINT_KEY}
    printer_info_url = OCTOPRINT_ROOT + 'api/printer'
    logger.info("Fetching printer data", url=printer_info_url)
    printer = requests.get(printer_info_url, headers=headers)
    logger.debug("Endpoint returned printer data", status=printer.status_code)
    if printer.status_code == 409:
        return "Not currently printing"

    printer_json = printer.json()
    logger.debug("Printer state is JSON", response=printer_json)
    flags = printer_json['state']['flags']
    printing = flags['printing']
    if not printing:
        return "Not currently printing"

    job_info_url = OCTOPRINT_ROOT + 'api/job'
    logger.info("Fetching job data")
    job = requests.get(job_info_url, headers=headers)
    logger.debug("Endpoint returned job data", status=job.status_code, response=job.json)

    progress = job.json()['progress']
    completion = progress['completion'] * 100
    print_time = progress['printTime']
    return f'~{completion:02d}% of the way through a job started at {print_time}'


def main():
    try:
        printer_status = get_printer_status()
    except Exception as e:
        logger.error("Error fetching snapshot", error=e)
        printer_status = 'Failed to retrieve printer status'

    try:
        logger.info("Fetching snapshot", url=SNAPSHOT_URL)
        snapshot = requests.get(SNAPSHOT_URL).content
    except RequestException as e:
        logger.error("Error fetching snapshot", error=e)
        snapshot = None

    if snapshot is None and printer_status is None:
        logger.error("Could not retrieve data! Exiting.")
        sys.exit(1)

    logger.info("PATCHing server image", url=PRINTER_ENDPOINT, username=USER, image_bytes=len(snapshot), printer_status=printer_status)
    response = requests.patch(PRINTER_ENDPOINT, auth=(USER, PASSWORD),
                              files={'status': printer_status,
                                     'image': None if snapshot is None else ('snapshot.jpg', snapshot, 'image/jpg')})

    if response.status_code != 200:
        logger.error("Failed to upload snapshot", status_code=response.status_code, content=response.json())
        sys.exit(2)

    logger.info("Successfully uploaded snapshot", content=response.json())


if __name__ == '__main__':
    structlog.configure(
        processors=[
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ]
    )
    main()
