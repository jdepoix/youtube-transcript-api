#!/usr/bin/env bash

.venv/bin/coverage run -m unittest discover && .venv/bin/coverage report
