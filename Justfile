default: run

run:
    poetry run python main.py run

initdb *args:
    poetry run python main.py initdb {{ args }}

setup:
    poetry install

lint:
    poetry run black --check archivebot
    poetry run isort --check-only archivebot
    poetry run flake8 archivebot

format:
    # remove unused imports
    poetry run autoflake \
        --remove-all-unused-imports \
        --recursive \
        --in-place archivebot
    poetry run black archivebot
    poetry run isort archivebot


# Watch for something
# E.g. `just watch lint` or `just watch test`
watch *args:
    watchexec --clear 'just {{ args }}'
