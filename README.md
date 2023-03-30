# ElevateAIEmailTest

This is an test app that retrieves an audio file from an email account, transcribes it using the Python ElevateAI API, and returns a text transcription back to the sender.

## Setup

A config.json is needed to defined parameters like IMAP host, username, password, etc.


## Usage

To test, send an email with "Transcribe" somewhere in the subject and attached an audio file. The app grabs the latest email with "Transcribe" in the subject and processes it with the ElevateAI API. Once transcription is completed, the transcription is sent back to the receiver with the subject "Completed Transcription."

This app was made using the sample.wav as the test audio file.
