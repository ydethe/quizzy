#! /bin/bash

pytest
mkdir -p htmldoc/quizzy
pdoc --html --force --config latex_math=True -o htmldoc quizzy
coverage html -d htmldoc/coverage --rcfile tests/coverage.conf
coverage xml -o htmldoc/coverage/coverage.xml --rcfile tests/coverage.conf
docstr-coverage src/quizzy -miP -sp -is -idel --skip-file-doc --badge=htmldoc/quizzy/doc_badge.svg
genbadge coverage -l -i htmldoc/coverage/coverage.xml -o htmldoc/quizzy/cov_badge.svg
