import boto3
from botocore.exceptions import BotoCoreError, ClientError
from contextlib import closing
from time import sleep
import os

from text_utils import chunk_text_to_lists

import config # Loads secret environment variables as globals

# import os
# import sys
# import subprocess
# from tempfile import gettempdir

# GLOBALS

# Secrets are loaded from environment variables in config.py
AWS_DEFAULT_POLLY_VOICE = "Matthew"
AWS_POLLY_TEXT_LIMIT = 2500 # 6000 characters, of which no more than 3000 can be "billed characters"
                            # You aren't billed for lexicon/SSML markup, so like 3000 real characters.
                            # So 3000 characters is the longest text you can send without a more complicated API.  
                            # Set lower to accomodate for adding '.' back in and some margin.


def save_polly_speech(basename, text, output_path, voice_id=AWS_DEFAULT_POLLY_VOICE):
    """Saves an .mp3 of speech corresponding to the text input."""

    # Get the Polly client
    try:
        polly = boto3.Session(  aws_access_key_id=AWS_ACCESS_KEY_ID,
                                aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
                                region_name='us-west-2').client('polly')
    except:
        print("ERROR: could not get polly client.")
        quit()

    # Breaks a long chunk of text into lists of text that are each under the limit, ending on sentence punctuation.
    text_chunks_list = chunk_text_to_lists(char_limit=AWS_POLLY_TEXT_LIMIT, text=text)

    total_chunks = len(text_chunks_list)
    for idx, chunk in enumerate(text_chunks_list):
        try:
            print(f"  requesting synthesis of length: {len(chunk)} chars..  ({idx+1}/{total_chunks})")
            # Request speech synthesis
            response = polly.synthesize_speech( Text=chunk,
                                                Engine="neural",
                                                OutputFormat="mp3",
                                                VoiceId=voice_id
                                                )
        except (BotoCoreError, ClientError) as error:
            # The service returned an error, exit gracefully
            print("ERROR: Error requesting polly speech response.")
            print(error)
            quit()

        # # Access the audio stream from the response
        # print(type(response))
        # print(response)

        # Example response:
        # {
        #     'ResponseMetadata': 
        #         {
        #             'RequestId': '260e15d3-1515-456a-aaca-1d5343fd90cf', 
        #             'HTTPStatusCode': 200, 
        #             'HTTPHeaders': {
        #                             'x-amzn-requestid': '260e15d3-1515-456a-aaca-1d5343fd90cf', 
        #                             'x-amzn-requestcharacters': '12', 
        #                             'content-type': 'audio/mpeg', 
        #                             'transfer-encoding': 'chunked', 
        #                             'date': 'Fri, 17 Dec 2021 17:53:39 GMT'
        #                             }, 
        #             'RetryAttempts': 0
        #         }, 
        #     'ContentType': 'audio/mpeg', 
        #     'RequestCharacters': '12', 
        #     'AudioStream': <botocore.response.StreamingBody object at 0x00000237EE8D2B80>
        # }

        if "AudioStream" in response:
            # Note: Closing the stream is important because the service throttles on the
            # number of parallel connections. Here we are using contextlib.closing to
            # ensure the close method of the stream object will be called automatically
            # at the end of the with statement's scope.
            with closing(response["AudioStream"]) as stream:
                # output = os.path.join(gettempdir(), "speech.mp3")

                try:
                    # Open a file for writing the output as a binary stream
                    with open(os.path.join(output_path, basename + "_" + str(idx+1) + ".mp3"), "wb") as file:
                        file.write(stream.read())
                except IOError as error:
                    # Could not write to file, exit gracefully
                    print("ERROR: Could not write to file.")
                    print(error)
                    quit()

        else:
            # The response didn't contain audio data, exit gracefully
            print("ERROR: Could not stream audio.")
            quit()

        # Throttle to keep lil' Polly happy.  Neural voice has burst limit of 10 transactions / second.
        sleep(0.15)