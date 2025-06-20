#!/bin/bash

# Load bash environment
source ~/.zshrc  # or .bashrc, .zshrc, etc., depending on your shell

# Update Homebrew itself
/opt/homebrew/bin/brew update

# Upgrade all installed packages
/opt/homebrew/bin/brew upgrade

# Optionally, cleanup old versions and cache
/opt/homebrew/bin/brew cleanup
