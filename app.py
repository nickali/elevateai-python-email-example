from ElevateAI import ElevateAI
import json
import time
import email
import imaplib
import os
import smtplib
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import tempfile
import sys

def get_newest_email_attachment(config):
    # Create temporary directory to save attachment
    tmp_folder = tempfile.mkdtemp()
    file_name = ''
    # Log in to the IMAP server
    imap_server = config['imap_server']
    imap_username = config['imap_username']
    imap_password = config['imap_password']
    imap = imaplib.IMAP4_SSL(imap_server)
    imap.login(imap_username, imap_password)
    print("Logged into IMAP server")

    # Select the INBOX folder
    imap.select("INBOX")

    # Search for the newest email message with an attachment
    search_criteria = 'DATE'
    result, data = imap.sort(search_criteria, 'UTF-8', 'ALL')
    latest_email_id = data[0].split()[-1]

    # Fetch the email message and extract the attachment
    result, data = imap.fetch(latest_email_id, "(RFC822)")
    raw_email = data[0][1]
    email_message = email.message_from_bytes(raw_email)

    attachment_path = None
    sender_address = None

    for part in email_message.walk():
        if part.get_content_maintype() == 'multipart':
            continue
        if part.get('Content-Disposition') is None:
            continue

        filename = part.get_filename()
        if not filename:
            continue

        # Save the attachment to a temporary file
        file_name = filename
        attachment_path = os.path.join(tmp_folder, filename)
        with open(attachment_path, 'wb') as f:
            f.write(part.get_payload(decode=True))

    # Get the sender email address
    sender_address = email.utils.parseaddr(email_message['From'])[1]

    # Log out of the IMAP server
    imap.close()
    imap.logout()

    return attachment_path, file_name, sender_address


def send_email_with_attachment(attachment_path, recipient_address, smtp_server, smtp_username, smtp_password):

  # Log in to the SMTP server
  smtp = smtplib.SMTP_SSL(smtp_server)
  smtp.ehlo()
  smtp.login(smtp_username, smtp_password)
  print("SMTP logged in.")
  # Create a message object
  message = MIMEMultipart()
  message['From'] = smtp_username
  message['To'] = recipient_address
  message['Subject'] = "Completed Transcription"

  # Add the attachment to the message
  with open(attachment_path, 'r') as f:
    attachment = MIMEApplication(f.read(), _subtype='txt')
    attachment.add_header('Content-Disposition', 'attachment', filename=os.path.basename(attachment_path))
    message.attach(attachment)

  # Send the message
  smtp.send_message(message)

  # Log out of the SMTP server
  smtp.quit()




def print_conversation(json_str):
  data = json.loads(json_str)
  filename = 'transcript.txt'
  
  # Initialize variables to store the accumulated phrases for each participant
  participantOne_phrases = ""
  participantTwo_phrases = ""
  tmp_folder = tempfile.mkdtemp()
  attachment_path = os.path.join(tmp_folder, filename)
  print("=== Begin Transcription Output ===\n\n")
  with open(attachment_path, 'w') as f:
    # Loop through the sentenceSegments list and accumulate phrases for each participant
    for segment in data['sentenceSegments']:
        if segment['participant'] == 'participantOne':
            participantOne_phrases += segment['phrase'] + " "
        elif segment['participant'] == 'participantTwo':
            participantTwo_phrases += segment['phrase'] + " "

        # If the next segment has a different participant, print the accumulated phrases and reset the variables
        if (data['sentenceSegments'].index(segment) != len(data['sentenceSegments'])-1) and (segment['participant'] != data['sentenceSegments'][data['sentenceSegments'].index(segment)+1]['participant']):
            p1 = participantOne_phrases.strip()
            p2 = participantTwo_phrases.strip()
            if p1:
              print("participantOne:\n" + p1 + "\n")
              f.write("participantOne:\n" + p1 + "\n\n")
            if p2:
              print("participantTwo:\n" + p2 + "\n")
              f.write("participantTwo:\n" + p2 + "\n\n")
            participantOne_phrases = ""
            participantTwo_phrases = ""

    # Print the accumulated phrases for the last participant
    p1 = participantOne_phrases.strip()
    p2 = participantTwo_phrases.strip()
    if p1:
      print("participantOne:\n" + p1 + "\n")
      f.write("participantOne:\n" + p1 + "\n\n")

    if p2:
      print("participantTwo:\n" + p2 + "\n")
      f.write("participantTwo:\n" + p2 + "\n\n")

    print("=== End Transcription Output ===\n\n")

  f.close()

  return attachment_path

def real_work(attach_path, file_name, config):

  #Prereq - make sure you create a free account @ https://app.elevateai.com - this will let you generate a token
  token = config["api_token"]
  langaugeTag = "en-us"
  vert = "default"
  transcriptionMode = "highAccuracy"
  localFilePath = attach_path
  fileName = file_name

  #Step 1,2
  declareResp = ElevateAI.DeclareAudioInteraction(langaugeTag, vert, None, token, transcriptionMode, False)

  declareJson = declareResp.json()

  interactionId = declareJson["interactionIdentifier"]
  print("Interaction Identifier: " + interactionId)

  #Step  3
  uploadInteractionResponse =  ElevateAI.UploadInteraction(interactionId, token, localFilePath, fileName)

  #Step 4
  #Loop over status until processed
  while True:
    getInteractionStatusResponse = ElevateAI.GetInteractionStatus(interactionId,token)
    getInteractionStatusResponseJson = getInteractionStatusResponse.json()
    if getInteractionStatusResponseJson["status"] == "processed" or getInteractionStatusResponseJson["status"] == "fileUploadFailed" or getInteractionStatusResponseJson["status"] == "fileDownloadFailed" or getInteractionStatusResponseJson["status"] == "processingFailed" :
          break
    time.sleep(15)

  #Step 6
  #get results after file is processed 
  getPuncutatedTranscriptResponse = ElevateAI.GetPuncutatedTranscript(interactionId, token)

  json_formatted_str = json.dumps(getPuncutatedTranscriptResponse.json(), indent=4)
  parsed_transcription = print_conversation(json_formatted_str)

  return parsed_transcription

def read_config(filename):
    """
    Read and parse the configuration file.
    """
    try:
        with open(filename, 'r') as f:
            config = json.load(f)
            required_fields = ['imap_server', 'imap_username', 'imap_password',
                               'smtp_server', 'smtp_username', 'smtp_password', 'api_token']
            for field in required_fields:
                if field not in config:
                    raise ValueError(f"Config file is missing required field: {field}")
            return config
    except FileNotFoundError:
        print(f'Error: Config file "{filename}" not found.')
        sys.exit(1)
    except json.JSONDecodeError:
        print(f'Error: Config file "{filename}" is not valid JSON.')
        sys.exit(1)
    except ValueError as e:
        print(f'Error: {e}')
        sys.exit(1)


def main():
  

    config = read_config('config.json')

    imap_server = config["imap_server"]
    imap_username = config["imap_username"]
    imap_password = config["imap_password"]
    smtp_server = config["smtp_server"]
    smtp_username = config["smtp_username"]
    smtp_password = config["smtp_password"]

    # Get the newest email attachment
    try:
        attach_path, filename, sender = get_newest_email_attachment(config)
    except imaplib.IMAP4.error:
        print('\nError connecting to the IMAP server or retrieving the email\n')
        return

    # Process the attachment and generate transcript
    try:
        transcript = real_work(attach_path, filename, config)
    except:
        print('\nError in transcribing\n')
        return
    
    if not os.path.exists(transcript):
        print('\nError finding the transcription file to send\n')
        return


    # Send email with transcript attachment
    try:
        send_email_with_attachment(
            transcript, 
            sender, 
            config['smtp_server'], 
            config['smtp_username'], 
            config['smtp_password']
        )
    except smtplib.SMTPException:
        print('\nError sending email through the SMTP server\n')
        return

 
main()
