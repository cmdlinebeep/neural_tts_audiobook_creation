"""Read out the tricky sentences and refine lexicon until it sounds correct."""

from text_utils import find_non_dictionary_words, get_unique_word_list, find_heteronyms, get_tricky_sentences, save_out_phoneme_dictionary
from tts_utils import save_polly_speech
import os

input_dir = input('Enter relative path to book folder containing input.txt file [e.g. books/hiroshima/]: ')   # e.g. books/hiroshima/
input_path = os.path.join(input_dir, "input.txt")

# get a unique list of words in the text
all_words_list = get_unique_word_list(input_path)

# get all non-English (tricky) words
all_non_english_words = find_non_dictionary_words(all_words_list)

# also get all heteronyms (words spelled the same that sound different) in the text
# homophone - new vs. knew
# homonym - pen (holding place for animals vs. writing instrument)
# heteronym / homograph - bass vs. bass (more specifically, don't have to pronounce differently, also could be called heteronyms)
# https://en.wiktionary.org/wiki/Category:English_heteronyms
all_heteronyms = find_heteronyms(all_words_list)

print(f"All tricky words in {input_path}:")
print(all_non_english_words)
print("")
print(f"All heteronyms in {input_path}:")
print(all_heteronyms)
print("")

# Saves output phoneme template file
save_out_phoneme_dictionary(input_dir=input_dir, input_word_list=all_non_english_words + all_heteronyms)  # append the lists together

# debug
# print(all_words_list)

tricky_sentences_list = get_tricky_sentences(file_dir=input_dir, words_to_check=all_non_english_words, return_all_matches=False)
heteronym_sentences_list = get_tricky_sentences(file_dir=input_dir, words_to_check=all_heteronyms, return_all_matches=True)

# Synthesize hard sentences with AWS Polly

# Build the text strings
text = ""
for line in tricky_sentences_list:
    text += line
print("Requesting and saving Non-English AWS Polly speech response..")
save_polly_speech(basename="non_english", text=text, voice_id="Matthew", output_path=input_dir)

print("")

text = ""
for line in heteronym_sentences_list:
    text += line
print("Requesting and saving Heteronyms AWS Polly speech response..")
save_polly_speech(basename="heteronyms", text=text, voice_id="Matthew", output_path=input_dir)

print("Finished.")