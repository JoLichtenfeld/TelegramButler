#!/bin/bash

# Define the Git repository URL and local directory
repo_url="https://github.com/JoLichtenfeld/TelegramButler"
local_dir="$HOME/TelegramButler"

# Navigate to the local directory
cd "$local_dir" || exit

# Perform a git pull to update the local repository
git pull

# Check if the git pull was successful
if [ $? -eq 0 ]; then
    echo "Git pull successful."
else
    echo "Error: Git pull failed. Please resolve any conflicts manually."
fi

# Run the Python script
python3 bot.py

    
