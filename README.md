# Neural TTS AudioBook Creation (using Amazon AWS Polly)

## Overview

I wanted to experiment with using the Amazon AWS Polly neural text-to-speech (TTS) model to see if it could handle creating an entire audiobook.

Using the API is simple and easy, and I had no issues there, but I'm not sure neural TTS is quite ready for this task (mind you, I tried this experiment back in December 2021 so it has probably come a long way since then).  The main issue I had was with some incorrect pronunciations.  I wanted to start with a tricky book with a lot of non-English words to really stress test it.  So I used the text from the original "Hiroshima" newspaper article from 1946, which contains many Japanese and German words.

To see how it handles these hard sentences, I built the function `read_tricky_sentences.py`, which finds all non-English words in the text and builds a short context sentence centered around that word, for example:

`Those who were burned moaned, “**mizu**, mizu! Water, water!” Mr. Tanimoto` (the script adds ** ** around the tricky word to call it out to the user, but it's not passed to the TTS)

Additionally, I had a hunch it would get certain heteronyms wrong (and it did).  Heteronyms are words with multiple possible pronunciations, based on the surrounding word context.  For example:

`With every number I read, my mind gets number and number.`

You can then listen to all the tricky sentences from the source text, and refine the lexicon until it sounds correct.  The lexicon is essentially an override telling the TTS how to say a given word, using its IPA pronunciation.  To update the lexicon, see the detailed instructions below involving a phonemes JSON file.  It will probably not read all sentences correctly the first time, unless you are using a simple text.

The meat of the code lies in `text_utils.py` and `tts_utils.py`.

`text_utils.py` contains functions for processing and manipulating text, both for sending to AWS but also for finding heteronyms and non-English words.  

`tts_utils.py` contains a single function for wrapping up any large string and sending it to AWS Polly TTS service.

## Get Started by Running the Demo

Create a virtual environment and install the Python packages in requirements.txt.

Then you'll need to sign up for the Amazon Polly API access.  Follow their instructions to end up with an `AWS_ACCESS_KEY_ID` and a `AWS_SECRET_ACCESS_KEY`, and set these as environment variables.  These will be loaded by `config.py` and therefore safe from ever being checked into version control.

At this point, try running `hello_polly.py` and make sure it works.  It should create two output files, `hello_polly.mp3` and `tricky_text.mp3` that you can listen to and ensures you have set up your environment correctly and configured things properly with Amazon.

## Creating your AudioBook

Next you'll need to create a `books\YOUR_BOOK\` directory at the base repo path, and create an `input.txt` file there with the source text you want Polly to read.  This path can be changed in `read_tricky_sentences.py` if you wish.  This folder is where it will create the tricky words .mp3 output files.  You'll spend most time here iterating and fixing the lexicon until things sound right.

Once you are ready to read the entire book, run `read_entire_book.py` to create the final output file.  This can take some time depending on the length of the book.



## Original (And Somewhat Outdated) Instructions for Creating Your AudioBook

All of this runs on the principle of least work.  That is, if the TTS gets something right by default, don't do anything!

### Iterative work:

1. Get full-text of book into a folder in /books/{title}/ in a file called input.txt
2. Run `python read_tricky_sentences.py`  which will create non_english_1.mp3, _2, _3 and
   heteronym_1.mp3, _2, _3, etc.  and spit out the corresponding text that is read into
   non_english_text.txt and heteronyms_text.txt files in the /books/{title}/ directory.
   It will also spit out a blank input_phonemes_TEMPLATE_DO_NOT_EDIT.json file in that
   same folder.  As mentioned by the name, this gets overwritten each time!
3. Manually listen to the above .mp3 files and read along to the text.
4. When the pronunciation is wrong, make a copy of input_phonemes_TEMPLATE_DO_NOT_EDIT.json 
   file, call it input_phonemes.json, and manually define phonemes for the tricky words.  
   A lot of the heteronyms will be right, so if they are, just delete their
   entry in the input_phonemes.json file.  Only delete these if the pronunciation of *every*
   instantiation is correct!  If input_phonemes.json file exists on a rerun,
   it will use those entries to make the output texts instead of the \*\*word\*\* formatting.  
5. Rerun steps 2 & 3, editing the phonemes JSON file, until the output .mp3 sound correct.
   Can use the online demo mode of whatever TTS using to get one at a time right without doing
   all of them at once.  Write down which exact instantiations of heteronyms it gets wrong, 
   as we'll want to fix only those later.

### Once all those steps have been iterated on until the text sounds good:

**NOTE** These steps not fully implemented yet!

6. Run `python read_entire_book.py` It will have the phonemes defined for all the tricky words.  For
   heteronyms, it will have EVERY occurrence of that word will have a \<phoneme\> tag surrounding
   the text.  Manually delete all except the ones we actually needed to correct (see earlier
   notes you made).  **NOTE** Need to implement the \<phoneme\> output tags.
7. Split input.txt manually into chapter_0.txt, chapter_1.txt, etc.  Use _0 for 
   books with like a preface or foreword.  Not strictly necessary but probably will want the 
   AudioBook separated into Chapters.
8. Run `python read_entire_book.py`  which will look for "chapter_{X}.txt" patterned files and 
   send them out to the TTS to generate final audio files.  **NOTE** Not implemented yet!
9. Send to production team for adding any static (unnaturally silent), enhance bass, etc.
10. Profit?