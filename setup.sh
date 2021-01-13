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

# if on a debian system
if [ -f /etc/debian_version ]; then
    # check if python3-venv is installed
    dpkg -s python3-venv > /dev/null 2>&1
    exit_status=$?
    if ! [ $exit_status -eq 0 ]; then
        echo -n "Looks like you're on a Debian system. This'll need python3-venv to set up a virtualenv, and I didn't find it. Should I try to install it (will ask for sudo password to install) (y/n)? "
        read answer
        if [ "$answer" != "${answer#[Yy]}" ]; then
            sudo apt-get install python3-venv
            exit_status=$?
            if ! [ $exit_status -eq 0 ]; then
                echo "Looks like installation didn't work. Try installing python3-venv yourself and rerunning this script."
                exit 2
            else
                echo "python3-venv sucessfully installed!"
            fi
        fi    
    fi
fi

# create a venv and add the required libraries to that venv
echo "Creating a virtualenv..."
$python -m venv ./venv

echo "Installing required packages..."
$python -m pip install -r requirements.txt

echo "Done!"