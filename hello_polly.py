"""
Getting Started Example
Used this test code to write save_polly_speech() in tts_utils.py
"""

import boto3
from botocore.exceptions import BotoCoreError, ClientError
from contextlib import closing

import config # Loads secret environment variables as globals

# Read secrets from environment variables
polly = boto3.Session(  aws_access_key_id=AWS_ACCESS_KEY_ID,
                        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
                        region_name='us-west-2').client('polly')

# Generate two pairs of text to test.  
# Second one tests some tricky heteronyms (words that have multiple pronunciations based on surrounding context)
text_examples = [
    ("hello_polly.mp3", "Hello polly, I mean, dolly!"),
    ("tricky_text.mp3", 
     """
    A bass was painted on the head of the bass drum.
    The buck does funny things when does are present.
    They were too close to the door to close it.
    Don't desert me here in the desert!
    When shot at, the dove dove into the bushes.
    The insurance was invalid for the invalid.
    How can I intimate this to my most intimate friend?
    With every number I read, my mind gets number and number.
    He could lead if he would get the lead out.
    I did not object to the object.

    minute:  the air-raid siren went off—a minute-long blast that warned of approaching planes
    minute:  a forty-five-minute trip to the tin works, in the section of town called Kannon-machi.

    <speak>
        You say: <phoneme alphabet="ipa" ph="pɪˈkɑːn">pecan</phoneme>. 
        I say: <phoneme alphabet="ipa" ph="ˈpi.kæn">pecan</phoneme>.
    </speak>
    """
    )
]

# Loop over the demo text
for (filename, text) in text_examples:
    try:
        # Request speech synthesis
        response = polly.synthesize_speech(Text=text, OutputFormat="mp3", VoiceId="Matthew")
    except (BotoCoreError, ClientError) as error:
        print(error)
        quit()

    # Access the audio stream from the response
    print(type(response))
    print(response)

    if "AudioStream" in response:
        # Note: Closing the stream is important because the service throttles on the
        # number of parallel connections. Here we are using contextlib.closing to
        # ensure the close method of the stream object will be called automatically
        # at the end of the with statement's scope.
        with closing(response["AudioStream"]) as stream:
            output = filename

            try:
                # Open a file for writing the output as a binary stream
                with open(output, "wb") as file:
                    file.write(stream.read())
            except IOError as error:
                # Could not write to file, exit gracefully
                print(error)
                quit()

    else:
        # The response didn't contain audio data, exit
        print("Could not stream audio")
        quit()