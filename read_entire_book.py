"""Read out the entire book once the lexicon has been refined."""

from tts_utils import save_polly_speech
import os

input_dir = input('Enter relative path to book folder containing input.txt file [e.g. books/hiroshima/]: ')   # e.g. books/hiroshima/
input_path = os.path.join(input_dir, "input.txt")

# Read in the entire book's text file
with open(input_path, 'r') as fr:
    entire_text = fr.read()   

# Synthesize the book with AWS Polly
print("Synthesizing entire book with AWS Polly, please wait..")

# NOTE: save_polly_speech() will automatically chunk the text to reasonable sizes for synthesis passes
save_polly_speech(basename="full_text", text=entire_text, output_path=input_dir)

print("Finished.")