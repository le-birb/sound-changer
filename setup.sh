#! /bin/sh

if [ -x "$(command -v python3)" ]; then
    python='python3'
elif [ -x "$(command -v python)" ]; then
    if [ "$(python --version)" == "Python 3."[89]* ]; then
        python='python'
    else
        echo "Python version 3.8 or higher not found"
        exit 1
    fi
fi

# create a venv and add the required libraries to that venv
$python -m venv ./venv
$python -m pip install -r requirements.txt