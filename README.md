# ElevateAI Python Email Example

This is an example where an audio file is retrieved from an email account, transcribed using the [Python ElevateAI API](https://github.com/NICEElevateAI/ElevateAIPythonSDK), and the transcription is sent back to the original sender.

## Setup

A config.json is needed to define parameters like IMAP host, username, password, etc.


## Usage

To test, send an email with "Transcribe" somewhere in the subject and attached an audio file. The app grabs the latest email with "Transcribe" in the subject and processes it with the ElevateAI API. Once transcription is completed, the transcription is sent back to the receiver with the subject "Completed Transcription."

This app was made using the sample.wav as the test audio file.
