"""

.. include:: ../../README.md

# Testing

## Run the tests

To run tests, just run:

    pytest

## Test reports

[See test report](../tests/report.html)

[See coverage](../coverage/index.html)

.. include:: ../../CHANGELOG.md

"""

import sys
import os
import logging


# création de l'objet logger qui va nous servir à écrire dans les logs
logger = logging.getLogger("uvicorn.error")
logger.setLevel(os.environ.get("LOGLEVEL", "info").upper())

# Create stream handler for stdout
logHandler = logging.StreamHandler(sys.stdout)

# JSON formatter
formatter = logging.Formatter(
    '{"time": "%(asctime)s", "level": "%(levelname)s", "message": "%(message)s", "name": "%(name)s"}'
)

logHandler.setFormatter(formatter)
logger.addHandler(logHandler)
