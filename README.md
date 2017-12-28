# Ask Alexa OneSphere

Python lambda function implementing a voice activated command console for OneSphere.

## Getting Started

This lambda function written in Python is an function that is triggered by an Alexa Skills Kit. There are three intents that are currently coded. They are:

- <b>BroHugDistance</b> A simple intent that returns a fixed utterance giving sage advice about giving a proper bro hug.
- <b> ServiceStatus</b> Performs a GET on the /rest/status API and returns the current service status.
- <b> TotalMonSpend</b> Performs a GET on the /rest/metrics API with query parameters 

The sample utterances that are tied to these intents are:
<br>
<br>
<b>BroHugDistance</b>
<br>

- "what is the right way to do a bro hug"
- "what should i remember when executing a bro hug"
- "what is a safe bro hug distance"

<br>
<b>ServiceStatus</b>
<br>

- "to report service status"
- "the latest status"
- "the latest service status"
- "the current status"
- "the current service status"
- "to report status"

<br>
<b>TotalMonSpend</b>
<br>

- "for the current total spend"
- "for the total monthly service spend"
- "what is the total montly spend"
- "for the total monthly spend"

The lambda function expects to have the following environment variables set:

- <b>api_base</b>  The URL base name for the OneSphere service (https://.../rest)
- <b>skill_id</b>  The skill_id to ensure no other trigger calls our lambda
- <b>user</b>      The user id for the local OneSphere user
- <b>password</b>  The password for the local OneSphere user

The credentials and the URL are essentially hard-coded in lambda environment variables. The code relies on the AWS KMS encryption for data-at-rest security. Certainly this is a hack and a better method should be implemented. When OneSphere supports identity providers then the code should implement linked identity. 

Here is a youtube video demonstrating the initial version of the code:

- <b> https://youtu.be/8Zu_I1sJhjk </b>

## Prerequisites

Ensure that the zip file that packages this skill for lambda includes the dependent Python libraries (i.e. requests). This code was tested against Python 2.7.

## What's New
171205 - Initial version.
<br>
171228 - Major restructuring of the code. Leveraged Anjishnu Kumar's excellent SDK for writing Alexa skills in Python. Added several new intents.

## Contributing

- The master branch is meant to be a stable version but the current master has had limited testing.
- All contributions are very much appreciated
- Feedback welcome (Wayland Jeong <wjeong@hpe.com>)

