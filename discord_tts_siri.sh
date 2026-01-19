#!/bin/zsh
# Zsh-friendly TTS script for Discord messages

# Join all arguments into a single string
MESSAGE="$*"

# Speak the message using Siri
say -v "Siri" "$MESSAGE"
