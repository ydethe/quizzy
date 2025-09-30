#! /bin/bash

uv run pytest
mkdir -p htmldoc/quizzy
uv run pdoc --html --force --config latex_math=True -o htmldoc quizzy
uv run coverage html -d htmldoc/coverage --rcfile tests/coverage.conf
uv run coverage xml -o htmldoc/coverage/coverage.xml --rcfile tests/coverage.conf
uv run docstr-coverage src/quizzy -miP -sp -is -idel --skip-file-doc --badge=htmldoc/quizzy/doc_badge.svg
uv run genbadge coverage -l -i htmldoc/coverage/coverage.xml -o htmldoc/quizzy/cov_badge.svg
