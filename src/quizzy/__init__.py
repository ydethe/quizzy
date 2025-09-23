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

from geopy.geocoders import Nominatim


# création de l'objet logger qui va nous servir à écrire dans les logs
logger = logging.getLogger("quizzy_logger")
logger.setLevel(os.environ.get("LOGLEVEL", "info").upper())

# Create stream handler for stdout
logHandler = logging.StreamHandler(sys.stdout)

# JSON formatter
formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s")

logHandler.setFormatter(formatter)
logger.addHandler(logHandler)

geolocator = Nominatim(user_agent="my_geocoder")
