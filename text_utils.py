"""Functions for text pre-processing to simplify audiobook creation."""

import regex    # NOT re, different library!
import re
import json
import os

# Globals

# compiled regular expression of punctuation to remove
# https://stackoverflow.com/a/39901522/2792686 
# https://en.wikipedia.org/wiki/Unicode_character_property#General_Category

# Doing this way will separate "don't" into "don" and "t" but has less noise
# But major problem with it explained below.
# REMOVE = regex.compile(r'[\p{C}|\p{M}|\p{P}|\p{S}|\p{Z}]+', regex.UNICODE)

# Doing this way will keep "don't" as a word but has more noise in it, like words at beginning or end of a quote
# Doing this way instead because can't split words on apostrophes, or can't easily put the whole word in lexicon
# e.g. 'domei’s' splits into 'domei' and 's' doing it the other way, but 'domei’s' is the word we need to define
# the custom lexicon for.  Downside of this way is contractions like "can’t" aren't in English dictionary.  But 
# TTS doesn't have issues with those, so just manually pruning those.
REMOVE = regex.compile(r'[\p{C}|\p{M}|\p{Ps}|\p{Pe}|\p{Po}|\p{Pc}|\p{Pd}|\p{S}|\p{Z}]+', regex.UNICODE)

# How many words before/after a tricky word to have the TTS read
CONTEXT_WORD_CNT = 7


def get_unique_word_list(filepath):
    '''Creates a list of unique words from a file path (plain text file)'''

    print("Tokenizing words in input text file..")

    all_words_set = set()

    try:
        with open(filepath, 'r', encoding='utf8') as inp:
            for line in inp:
                # print(line)

                depunctuated_line = REMOVE.sub(" ", line).strip()
                # print(depunctuated_line)
                
                for word in depunctuated_line.split():
                    # print(word)
                    
                    # Add lowercased word to set. Also strip off “
                    all_words_set.add(re.sub('[“”]', '', word).lower().strip())
                    # all_words_set.add(word.lower())
    except FileNotFoundError:
        print(f"Cannot find file path: {filepath}")
        print("Ensure input file is named 'input.txt' and directory is spelled correctly.")
        quit()

    # convert set to list so we can sort it by length
    all_words_list = list(all_words_set)

    # sort it, shortest to longest words, just cause
    all_words_sorted = list(sorted(all_words_list, key = len))

    return all_words_sorted


def find_non_dictionary_words(input_word_list):
    """Takes a list of words and returns a list of the ones that aren't English words,
    as defined by what's in an English dictionary"""

    # Got a JSON file of English words from this site
    # https://github.com/dwyl/english-words

    print("Loading English word dictionary reference..")
    with open('words_english_dictionary.json', 'r') as ed_file:
        english_words = json.load(ed_file)

    non_english_words = []

    for word in input_word_list:
        if word not in english_words:
            # print(f"{word} is not an English word.")
            
            # Also make sure it's not just a number, the TTS doesn't have problems with these
            if not word.isnumeric():

                # Also, make sure it's not like 1st, 2nd, 3rd, 4th, etc., the TTS handles those well
                if not re.match("^\d+(st|nd|rd|th)$", word):

                    # Also, make sure not just one of these common contractions
                    if not (word == "didn’t" or word == "he’s" or word == "don’t" or word == "he’ll" \
                        or word == "can’t" or word == "i’ll" or word == "it’s" or word == "we’re" \
                        or word == "won’t" or word == "that’s" or word == "aren’t" or word == "you’re" \
                        or word == "she’s" or word == "she’ll" or word == "we’ll" or word == "who’s" \
                        or word == "won’t" or word == "shouldn’t" or word == "haven’t" or word == "hadn’t" \
                        or word == "you’ll" or word == "they’re" or word == "doesn’t" or word == "i’m" \
                        or word == "else’s" or word == "you’ve" or word == "there’s" or word == "they’ll" \
                        or word == "couldn’t"):

                        # NOTE: Do NOT add possessives, like "father’s" as often these are people's names, like "Matsumoto’s"
                        # and those will need pronunciation help!

                        # NOTE: Too noisy still.  Tons of possessive words like "father’s" and "mission’s" in there, as well 
                        # as words that start with a single quote like: '‘what'
                        # What I want to do is, strip off "’s" and check if word stem is English word, if so, ignore it.

                        # >>> "O’Reilley".split("’s")       # Won't break words that have ’s in middle
                        # ['O’Reilley']
                        # >>> "textbook".split("’s")        # Safe to do on word with no ’s
                        # ['textbook']
                        # >>> "Nakamura’s".split("’s")      # For possessives, [0]th entry will contain the word we're after
                        # ['Nakamura', '']
                        stem_word = word.split("’s")[0]

                        if stem_word not in english_words:
                            # Adds "nakamura", for example

                            # But also want to strip off leading or trailing ’
                            # like jesuits’ or ’Tis or ‘Tis
                            stripped_word = word.strip("’")
                            stripped_word = stripped_word.strip("‘")

                            if (stripped_word != '') and (stripped_word != '’') and (stripped_word != "‘") \
                                and (stripped_word not in english_words):
                                non_english_words.append(word)
                            else:
                                # print(f"stripped_word: {stripped_word}")
                                pass
                        else:
                            # print(f"stem_word: {stem_word}")
                            pass

    return non_english_words


def find_heteronyms(input_word_list):
    '''Find heteronyms in the text.'''

    print("Loading English heteronyms..")
    heteronyms_found = []
    with open("heteronyms.txt", 'r', encoding='utf8') as inp:
        for hetero in inp:
            if hetero[0] == '#':
                # Allow me to comment out heteronyms in file.  For example, 
                # 'are' is a heteronym, like a hectare but a single one.  
                # Super rare case and makes lots of noise for me.
                continue    # skip this word
            for input_word in input_word_list:
                # all are lowercase already, one per line on file
                # input_words already guaranteed stripped of space
                if input_word == hetero.strip():
                    heteronyms_found.append(input_word)
                    break
    
    return heteronyms_found


def save_out_phoneme_dictionary(input_dir, input_word_list):
    """Saves out a JSON format of all the words that may be copy/pasted into input_phonemes_TEMPLATE_DO_NOT_EDIT.json
    This file will let you manually use IPA pronunciation overrides for any words the TTS gets wrong."""

    # {
    #     "zu": {
    #         "alphabet": "ipa",
    #         "ph": "pɪˈkɑːn"
    #     },
    #     "b1": {
    #         "alphabet": "ipa",
    #         "ph": "pɪˈkɑːn"
    #     },
    #     "mizu": {
    #         "alphabet": "ipa",
    #         "ph": "pɪˈkɑːn"
    #     }
    # }
    with open(os.path.join(input_dir, "input_phonemes_TEMPLATE_DO_NOT_EDIT.json"), "w", encoding="utf8") as fw:
        fw.write("{\n")
        for idx, word in enumerate(input_word_list):
            fw.write(f"    \"{word}\": {{\n")                # \{ doesn't work, curly brackets in f-string need double to escape
            fw.write(f"        \"alphabet\": \"ipa\",\n")
            fw.write(f"        \"ph\": \"\"\n")
            if (idx + 1) == len(input_word_list):
                fw.write("    }\n")
            else:
                fw.write("    },\n")
        fw.write("}")
        
        # print("Printing a copy/paste version of blank entries for input_phonemes.json file:")
        # print("")
        # print("{")
        # for idx, word in enumerate(input_word_list):
        #     print(f"    \"{word}\": {{")                # \{ doesn't work, curly brackets in f-string need double to escape
        #     print(f"        \"alphabet\": \"ipa\",")
        #     print(f"        \"ph\": \"\"")
        #     if (idx + 1) == len(input_word_list):
        #         print("    }")
        #     else:
        #         print("    },")
        # print("}")
        # print("")

    
def get_tricky_sentences(file_dir, words_to_check, return_all_matches):
    '''Takes a list of words and returns the words around it in that line 
    of the file that contains it, to see context.  Returns either just the
    first matching word (for non-English words) or all matches (use for heteronyms).'''

    filepath = os.path.join(file_dir, "input.txt")
    print(f"Grabbing context sentences from input file {filepath}..")

    phonemes_path = os.path.join(file_dir, "input_phonemes.json")

    # See if the input_phonemes.json file already exists
    # print(f"Load custom phonemes for this text ({phonemes_path})..")
    first_run = False
    try:
        pf = open(phonemes_path, 'r', encoding='utf8')
    except FileNotFoundError:
        # input_phonemes.json file doesn't exist yet, use **{word}** formatting in output
        first_run = True
    else:
        phonemes = json.load(pf)
        pf.close()

    # with open(phonemes_path, 'r', encoding='utf8') as phonemes_file:
    #     # phonemes is a python dictionary
    #     phonemes = json.load(phonemes_file)

    all_sentences_list = []
    
    # iterate over tricky words
    for word in words_to_check:
        try:
            # reopen the file each time for each word, otherwise cursor just continues to end of file
            with open(filepath, 'r', encoding='utf8') as inp:
            
                # iterate over every line in file
                for line in inp:
                    # print(line)

                    # Try a line-by-line basis and just grab X *characters* around the words instead of on 
                    # word boundaries.  That way, wherever the word is in the line, it'll replace it.
                    lower_line = line.lower()

                    # Tries to find if the word in this line, if it's there
                    pattern = re.compile(f"\\b{word}\\b")   # \b for word boundary, but need double escape, or get \x08 (backspace char)
                    m = pattern.search(lower_line)

                    if m:
                        # was a match
                        start = m.start()   # index of match start
                        end = m.end()       # index of match end
                    else:
                        # no match in this line, skip it and move on to next one
                        continue

                    try:
                        # NOTE: Will have to hear how these sound, then just define the ones that need help.
                        # On the first run, puts ** ** around the word.  After you've defined an input_phonemes.json
                        # file, then it uses those.  
                        if first_run:
                            phonemed_sentence = (line[start-(CONTEXT_WORD_CNT*5):start] + '**' + word \
                                + "**" + line[end:end+(CONTEXT_WORD_CNT*5)]).strip()        # Strip newlines off for consistency
                        else:
                            phonemed_sentence = (line[start-(CONTEXT_WORD_CNT*5):start] + '<phoneme alphabet="' \
                            + phonemes[word]['alphabet'] + '" ph="' + phonemes[word]['ph'] + '">' + word \
                            + "</phoneme>" + line[end:end+(CONTEXT_WORD_CNT*5)]).strip()

                    except KeyError:
                        # If a KeyError occurs, then that means that there is no entry for phonemes[word].
                        # This most likely means that we deleted that as a tricky word, and want the TTS
                        # to just pronounce it as its default method.
                        # Just skip this line of the file (effectively skips this word) and don't have 
                        # any sentences with this word in the output files.
                        continue

                    # print(f"{word}:  {context_sentence}")
                    # print(f"{phonemed_sentence}")
                    # all_sentences_list.append(f"{word}:  {context_sentence}")
                    all_sentences_list.append(f"{phonemed_sentence}")
                    
                    # This is the key usage different right here.
                    # For heteronyms, they can be used multiple times in the file and each time pronounced differently.
                    # The non-English words are likely to be pronounced the same each time.
                    if not return_all_matches:
                        break

        except FileNotFoundError:
            print(f"Cannot find file path: {filepath}")
            quit()

    # print("")

    # Save the lines to files too
    if return_all_matches:
        # This is the case we're looking at the heteronyms
        outfile = os.path.join(file_dir, "heteronyms_text.txt")
    else:
        # Otherwise, it's the non-English words file
        outfile = os.path.join(file_dir, "non_english_text.txt")

    with open(outfile, "w", encoding="utf8") as fw:
        for line in all_sentences_list:
            fw.write(line + '\n')
        print(f"Saved output text file: {outfile}.\n")

    # Also return the lines, they'll go on to be sent to the TTS engine
    return all_sentences_list


def chunk_text_to_lists(char_limit, text):
    """Returns an array of text broken on sentence boundaries, with max=char_limit lengths"""

    # NOTE: If char_limit is unreasonably small, function breaks
    if char_limit < 50:
        print("ERROR: Use larger text chunking limit to support chunk_text_to_lists().")
        print(f"AWS Polly supports up to roughly 3000 characters at a time.  You used {char_limit}. Quitting.")
        quit()
    
    # https://www.regular-expressions.info/lookaround.html
    # https://stackoverflow.com/questions/12689046/multiple-negative-lookbehind-assertions-in-python-regex/12689275
    # s = """Hello. This sentence ends with a letter. It's good to meet you, Mr. Makamoto!  I've heard great things, and have you met my wife, Mrs. Baby, shes awesome and
    # my name is Dr. Bob. Would you take a seat, please?  Please, Ms. Jane."""
    # re.split(r"(?<!Mr)(?<!Dr)(?<!Mrs)(?<!Ms)[.\n]", s)
    # ['Hello', ' This sentence ends with a letter', " It's good to meet you, Mr. Makamoto!  I've heard great things, and have you met my wife, Mrs. Baby, shes awesome and", 'my name is Dr. Bob', ' Would you take a seat, please?  Please, Ms. Jane', '']

    # Split the sentences on dots AND newlines, UNLESS dot is preceded by an honorific title, like Mrs., Mr., or Dr.
    sentences = re.split(r"(?<!Mr)(?<!Dr)(?<!Mrs)(?<!Ms)(?<!Miss)[.\n]", text)

    # Split the sentences on dots ONLY (no newlines), UNLESS dot is preceded by an honorific title, like Mrs., Mr., or Dr.
    # sentences = re.split(r"(?<!Mr)(?<!Dr)(?<!Mrs)(?<!Ms)(?<!Miss)[.]", text)

    # Split text on periods first
    # old way:
    # sentences = text.split('.')
    
    # doesn't include the periods
    # print(f"{sentences[0]}")
    # print(f"{sentences[-1]}")

    all_chunks = []
  
    # Iterate over all the sentences
    cur_string = ''
    for next_sentence in sentences:
        # If adding the next sentence to the current string would exceed the limit,
        # start a new string
        if (len(cur_string) + len(next_sentence)) >= char_limit:
            # First add the current string to list of chunks
            all_chunks.append(cur_string)

            # Start new list, seed it with this next sentence since we've already iterated on it, with period
            cur_string = next_sentence + '.'
        else:
            # Otherwise, we can safely add it to the current string, plus trailing period which was stripped
            cur_string += (next_sentence + '.')
    else:
        # This runs at the end of the for loop
        # Don't forget to append final cur_string
        all_chunks.append(cur_string)

    # print(all_chunks[0][-60:])
    # print("")
    # print(all_chunks[1][-60:])
    # print("")
    # print(all_chunks[2][-60:])
    # print("")
    # print(all_chunks[-2][-60:])
    # print("")
    # print(all_chunks[-1][-60:])

    return all_chunks
   


# Test chunk_text_to_lists

# Non-English Words:

# text = \
# '''
# b1:  time to give him injections of 'Vitamin B1.' A Buddhist priest with whom Mr. Hi.
# zu:  zu machen. There’s nothing to be done about it.”
# 9th:  On August 9th, Father Kleinsorge was still tired. The
# b29:  a professional eye as a B29. “There goes Mr. B!” he shouted.
# 29s:  time the B-29s were using Lake Biwa, northeast of Hiroshima, as a rendezvous point,
# ota:  out from the Ota River; its main commercial and residential districts, covering about four
# nai:  “Shikata ga nai,” a Japanese expression as common as, and corresponding to, the Russian
# drs:  The lot of Drs. Fujii, Kanda, and Machii right after
# 1st:  coming back by the thousand—by November 1st, the population, mostly crowded into the outskirts,
# 8th:  On the third day, August 8th, some friends who supposed she was dead came
# und:  in der linken Unterschenkelgegend. Haut und sichtbare Schleimhäute mässig durchblutet und kein Oedema,” noting
# kyo:  water of the Kyo River, and next to the bridge of the same name,
# 7th:  Early. that day, August 7th, the Japanese radio broadcast for the
# 17th:  and heavily. The river rose. On September 17th, there came a cloudburst and then
# kabe:  sick, went to the nearby town of Kabe and moved in with Mrs. Nakamura’s
# 20th:  she dressed on the morning of August 20th, in the home of her sister-in-law
# kimi:  One of the girls begun to sing Kimi ga yo, national anthem, and others
# yano:  only two patients left—a woman from Yano, injured in the shoulder, and a young
# kobe:  Middle School in Kobe and which he wore during air-raid alerts.
# mizu:  bleeding. Those who were burned moaned, “Mizu, mizu! Water, water!” Mr. Tanimoto found a
# 23rd:  an incision in her leg on October 23rd, to drain the infection, which still
# kaba:  that animal is kaba, the reverse of baka, stupid. He told Bible stories, beginning,
# 19th:  from the hospital in Tokyo on December 19th and took a train home. On
# 18th:  On August 18th, twelve days after the Mr. bomb burst,
# 11th:  the park, Mr. Tanimoto returned, on August 11th, to his parsonage and dug around
# 12th:  on August 12th: “There is nothing to do but admit the tremendous power of
# sato:  excited when he saw his friend Seichi Sato riding up the river in a
# 26th:  practically in hiding. On August 26th, both she and her younger daughter, Myeko, woke
# 15th:  had died on February 15th, the day Singapore fell, and that he had been
# kure:  of mass raids on Kure, Iwakuni, Tokuyama, and other nearby towns; he was sure
# zeit:  magazine, Stimmen der Zeit; Dr. Terufumi Sasaki, a young member of the surgical staff
# kein:  sichtbare Schleimhäute mässig durchblutet und kein Oedema,” noting that she was a medium-sized female
# gion:  that he ran north two miles to Gion, a suburb in the foothills. All
# 10th:  meal they were offered. On August 10th, a friend, Mrs. Osaki, came to see
# akio:  to do. Her eleven-month-old brother, Akio, had come down the day before with a
# tsuzu:  on the Inland Sea near Tsuzu, the man with whom Mr. Tanimoto’s mother-in-law and
# kamai:  across a twenty-year-old girl, Mrs. Kamai, the Tanimotos’ next-door neighbor. She was crouching on
# tansu:  that their burden was to be a tansu, a large Japanese cabinet, full of
# neher:  and Neher electrometers; they understood the idea all too well.
# osaki:  On August 10th, a friend, Mrs. Osaki, came to see them and told them
# kanda:  death, and suggested either Dr. Kanda, who lived on the next corner, or Dr.
# getty:  Photograph from Rolls Press / Popperfoto
# myeko:  and dressed them and walked with them to the military area known as the
# mâché:  the room, but a mere papier-mâché suitcase, which he had hidden under the desk,
# gutem:  his records: “Mittelgrosse Patientin in gutem Ernährungszustand. Fraktur am linken Unterschenkelknochen mit Wunde; Anschwellung
# wunde:  Fraktur am linken Unterschenkelknochen mit Wunde; Anschwellung in der linken Unterschenkelgegend. Haut und sichtbare
# okuma:  house of a friend of his named Okuma, in the village of Fukawa, asked
# tamai:  and over, “Shu Jesusu, awaremi tamai! Our Lord Jesus, have pity on us!”
# rokko:  teaching at the Rokko Middle School in Kobe and which he wore during air-raid
# fukai:  the mission house; Mr. Fukai, the secretary of the diocese; Mrs. Murata, the mission’s
# asahi:  down cross-legged to read the Osaka Asahi on the porch of his private hospital,
# ujina:  trace them through the post office in Ujina, a suburb of Hiroshima. Still later,
# fujii:  desk. At that same moment, Dr. Masakazu Fujii was settling down cross-legged to read
# shima:  been the Shima Hospital. (A few vague human silhouettes were found, and these gave
# taiko:  I went to Taiko Bridge and met my girl friends Kikuki and Murakami. They
# hideo:  and told them that her son Hideo had been burned alive in the factory
# heika:  father followed after his son, ‘Tenno-heika, Banzai, Banzai, Banzai!’ In the result, Dr. Hiraiwa
# asano:  away with her to the woods in Asano Park—an estate, by the Kyo River
# kisen:  officer of the Toyo Kisen Kaisha steamship line, an anti-Christian, a man famous in
# yaeko:  and a five-year-old girl, Myeko—out of bed and dressed them and walked with them
# ushida:  spend nights with a friend in Ushida, a suburb to the north. Of all
# kyushu:  two daughters were in the country on Kyushu. A niece was living with him,
# kayoko:  “Miss Kayoko Nobutoki, a student of girl’s high
# machen:  machen. There’s nothing to be done about it.”
# gokoku:  on the torii gateway of the Gokoku Shrine, right next to the parade ground
# gotted:  I have gotted my mind to dedicate what I have and to complete the
# matsui:  The rayon man, a Mr. Matsui, had opened his then unoccupied estate to a
# mässig:  Unterschenkelgegend. Haut und sichtbare Schleimhäute mässig durchblutet und kein Oedema,” noting that she was
# hataya:  A nervous neighbor, Mrs. Hataya, called to Mrs. Nakamura to run
# seichi:  quite excited when he saw his friend Seichi Sato riding up the river in
# hersey:  By John Hersey
# fukawa:  his named Okuma, in the village of Fukawa, asked Father Cieslik if he would
# tamura:  had taken him to the Tamura Pediatric Hospital and was staying there with him.
# kikuki:  my girl friends Kikuki and Murakami. They were looking for their mothers. But Kikuki’s
# fukai’:  theological student came up and grabbed Mr. Fukai’ s feet, and Father Kleinsorge took
# matsuo:  A friend of his named Matsuo had, the day before, helped him get the
# genshi:  this word-of-mouth report as genshi bakudan—the root characters of which can be translated as
# linken:  in gutem Ernährungszustand. Fraktur am linken Unterschenkelknochen mit Wunde; Anschwellung in der linken Unterschenkelgegend.
# misasa:  them into the river. At Misasa Bridge, they encountered a long line of soldiers
# jesusu:  crying over and over, “Shu Jesusu, awaremi tamai! Our Lord Jesus, have pity on
# honshu:  two hundred B-29s were approaching southern Honshu and advised the population of Hiroshima to
# kaisha:  of the Toyo Kisen Kaisha steamship line, an anti-Christian, a man famous in Hiroshima
# fiancé:  she would always be a cripple. Her fiancé never came to see her. There
# sasaki:  atomic bomb flashed above Hiroshima, Miss Toshiko Sasaki, a clerk in the personnel department
# takasu:  Takasu, thirty-three hundred yards from the center, they learned some far more important facts
# machii:  he encountered a friend, a doctor named Machii, and asked in bewilderment, “What do
# nobori:  lived in the section called Nobori-cho and who had long had a habit of
# façade:  stone façade of a bank building on which he was at work, in the
# toshio:  boy, Toshio, an eight-year-old girl, Yaeko, and a five-year-old girl, Myeko—out of bed and
# siemes:  using the bomb. One of them, Father Siemes, who was out at Nagatsuka at
# fukuro:  the part of town called Fukuro, and besides, she felt drawn by some fascination,
# kannon:  called Kannon-machi. She was in charge of the personnel records in the factory. She
# murata:  of the diocese; Mrs. Murata, the mission’s devoutly Christian housekeeper; and his fellow-priests. After
# myeko’s:  began gradually to feel better. Some of Myeko’s hair fell out, and she had
# asanos’:  to one of the pools in the Asanos’ rock gardens and got water for
# bakudan:  word-of-mouth report as genshi bakudan—the root characters of which can be translated as “original
# o’clock:  Reverend Mr. Tanimoto got up at five o’clock that morning. He was alone in
# hiraiwa:  “Dr. Y. Hiraiwa, professor of Hiroshima University of Literature
# suntory:  perfectly satisfied with the best Japanese brand, Suntory.
# stimmen:  a Jesuit magazine, Stimmen der Zeit; Dr. Terufumi Sasaki, a young member of the
# cochère:  the front hall, and under the porte-cochère, and on the stone front steps, and
# zempoji:  the statisticians began to say that at least a hundred thousand people had lost
# fujii’s:  the local circle of destruction to Dr. Fujii’s private hospital, on the bank of
# awaremi:  over and over, “Shu Jesusu, awaremi tamai! Our Lord Jesus, have pity on us!”
# gambare:  as only a Japanese would, “Sasaki, gambare! Be brave!” Just then (the building was
# curated:  Read classic New Yorker stories, curated by our archivists and editors.
# gropper:  and double-braced by a priest named Gropper, who was terrified of earthquakes; that the
# sankoku:  only capital was a Sankoku sewing machine. After his death, when his allotments stopped
# kiyoshi:  the Reverend Mr. Kiyoshi Tanimoto, pastor of the Hiroshima Methodist Church, paused at the
# shikoku:  to his father’s home in Shikoku. There he rested another month.
# iwasaki:  sick and prostrate. A woman named Iwasaki, who lived in the neighborhood of the
# okuma’s:  in a terribly hot sun to Mr. Okuma’s house, which was beside the Ota
# yoshida:  belonged, was an energetic man named Yoshida. He had boasted, when he was in
# groweth:  morning they are like grass which groweth up. In the morning it flourisheth and
# domei’s:  such as Domei’s assertion on August 12th: “There is nothing to do but admit
# hatsuyo:  deltaic rivers which divide Hiroshima; Mrs. Hatsuyo Nakamura, a tailor’s widow, stood by the
# kamai’s:  a chance of finding Mrs. Kamai’s husband, even if he searched, but he wanted
# kataoka:  before. He learned that their name was Kataoka; the girl was thirteen, the boy
# cieslik:  two days, along with Father Cieslik, a fellow-priest, from a rather painful and urgent
# iwakuni:  mass raids on Kure, Iwakuni, Tokuyama, and other nearby towns; he was sure Hiroshima’s
# kanda’s:  blood, came back and said that Dr. Kanda’s house was ruined and that fire
# chugoku:  to read that morning’s Hiroshima Chugoku. To her relief, the all-clear sounded at eight
# toshiko:  the atomic bomb flashed above Hiroshima, Miss Toshiko Sasaki, a clerk in the personnel
# molotov:  must have been a Molotoffano hanakago”—a Molotov flower basket, the delicate Japanese name for
# lasalle:  section—Father Superior LaSalle and Father Schiffer—had happily escaped this affliction.
# nakamura:  rivers which divide Hiroshima; Mrs. Hatsuyo Nakamura, a tailor’s widow, stood by the window
# tsingtao:  at the Eastern Medical University, in Tsingtao, China. He was something of an idealist
# inokuchi:  station in the section of Inokuchi, where two Army doctors looked at her. The
# laderman:  shack, and he and another priest, Father Laderman, who had joined him in the
# hirohito:  very moment, the dull, dispirited voice of Hirohito, the Emperor Tenno, was speaking for
# nobutoki:  “Miss Kayoko Nobutoki, a student of girl’s high school,
# yokogawa:  turned far left and ran out to Yokogawa, a station on a railroad line
# jazabuin:  a student of girl’s high school, Hiroshima Jazabuin, and a daughter of my church
# boundage:  civilians, all of them were in boundage, some being helped by shoulder of their
# terufumi:  der Zeit; Dr. Terufumi Sasaki, a young member of the surgical staff of the
# carriest:  a watch in the night. Thou carriest the children of men away as with
# kikuki’s:  their mothers. But Kikuki’s mother was wounded and Murakami’s mother, alas, was dead.”
# murakami:  friends Kikuki and Murakami. They were looking for their mothers. But Kikuki’s mother was
# tanimoto:  Reverend Mr. Kiyoshi Tanimoto, pastor of the Hiroshima Methodist Church, paused at the door
# tokuyama:  raids on Kure, Iwakuni, Tokuyama, and other nearby towns; he was sure Hiroshima’s turn
# tasukete:  heard two small voices crying, “Tasukete! Tasukete! Help! Help!”
# nakamoto:  and hurried to the house of Mr. Nakamoto, the head of her Neighborhood Association,
# masakazu:  next desk. At that same moment, Dr. Masakazu Fujii was settling down cross-legged to
# sasaki’s:  Sasaki had been walking was dead; Dr. Sasaki’s patient, whom he had just left
# matsuo’s:  that morning, Mr. Tanimoto started for Mr. Matsuo’s house. There he found that their
# schiffer:  and Father Schiffer—had happily escaped this affliction.
# grummans:  near the Nakamura family shouted, “It’s some Grummans coming to strafe us!” A baker
# bokuzuki:  shoes, padded-cotton air-raid helmets called bokuzuki, and even, irrationally, overcoats. The children were silent,
# takemoto:  only worshippers were Mr. Takemoto, a theological student living in the mission house; Mr.
# sandspits:  to make an announcement—alongside the crowded sandspits, on which hundreds of wounded lay; at
# nakashima:  to strafe us!” A baker named Nakashima stood up and commanded, “Everyone who is
# matsumoto:  around for other friends. He saw Mrs. Matsumoto, wife of the director of the
# yamaguchi:  in from the city of Yamaguchi with extra bandages and antiseptics, and the third
# nagatsuka:  his parental house, in the suburb of Nagatsuka. He asked Dr. Machii to join
# kaitaichi:  heard about a vacant private clinic in Kaitaichi, a suburb to the east of
# ninoshima:  to the nearby island of Ninoshima, and she was taken to a military hospital
# hoshijima:  The daughter of Mr. Hoshijima, the mission catechist, ran up to
# narucopon:  someone had found intact a supply of narucopon, a Japanese sedative, and he gave
# patientin:  wrote all his records: “Mittelgrosse Patientin in gutem Ernährungszustand. Fraktur am linken Unterschenkelknochen mit
# withereth:  evening it is cut down, and withereth. For we are consumed by Thine anger
# mukaihara:  night before. His mother’s home was in Mukaihara, thirty miles from the city, and
# lauritsen:  with Lauritsen electroscopes and Neher electrometers; they understood the idea all too well.
# nakamuras:  their friends as they passed, the Nakamuras were all sick and prostrate. A woman
# sichtbare:  der linken Unterschenkelgegend. Haut und sichtbare Schleimhäute mässig durchblutet und kein Oedema,” noting that
# kalamazoo:  of Kalamazoo, as its adviser, began to consider what sort of city the new
# popperfoto:  Photograph from Rolls Press / Popperfoto
# cookstoves:  caused by inflammable wreckage falling on cookstoves and live wires), Mrs. Nakamura suggested going
# murakami’s:  was wounded and Murakami’s mother, alas, was dead.”
# wassermann:  specimen for a Wassermann test in his hand; and the Reverend Mr. Kiyoshi Tanimoto,
# schiffer’s:  Father Kleinsorge stemmed Father Schiffer’s spurting cut as well as he
# tanimoto’s:  the man with whom Mr. Tanimoto’s mother-in-law and sister-in-law were living, saw the flash
# tanimotos’:  twenty-year-old girl, Mrs. Kamai, the Tanimotos’ next-door neighbor. She was crouching on the ground
# nakamura’s:  of Kabe and moved in with Mrs. Nakamura’s sister-in-law. The next day, Mrs. Nakamura,
# eyesockets:  wholly burned, their eyesockets were hollow, the fluid from their melted eyes had run
# kleinsorge:  fire lane; Father Wilhelm Kleinsorge, a German priest of the Society of Jesus, reclined
# tonarigumi:  of his local tonarigumi, or Neighborhood Association, and to his other duties and concerns
# nagaragawa:  the close-packed residential district called Nagaragawa, to a house that belonged to a rayon
# flourisheth:  groweth up. In the morning it flourisheth and groweth up; in the evening it
# durchblutet:  Haut und sichtbare Schleimhäute mässig durchblutet und kein Oedema,” noting that she was a
# hatsukaichi:  with it. She was taken ashore at Hatsukaichi, a town several miles to the
# hoshijima’s:  of the kitchen, he saw Mrs. Hoshijima’s head. Believing her dead, he began to
# molotoffano:  Machii said, “It must have been a Molotoffano hanakago”—a Molotov flower basket, the delicate
# largeaugust:  A Reporter at LargeAugust 31, 1946 Issue
# macarthur’s:  headquarters systematically censored all mention of the bomb in Japanese scientific publications, but soon
# anschwellung:  am linken Unterschenkelknochen mit Wunde; Anschwellung in der linken Unterschenkelgegend. Haut und sichtbare Schleimhäute
# kleinsorge’s:  now, beat on Father Kleinsorge’s shoulders and said, “I won’t leave. I won’t leave.”
# schleimhäute:  linken Unterschenkelgegend. Haut und sichtbare Schleimhäute mässig durchblutet und kein Oedema,” noting that she
# electrometers:  Neher electrometers; they understood the idea all too well.
# ernährungszustand:  records: “Mittelgrosse Patientin in gutem Ernährungszustand. Fraktur am linken Unterschenkelknochen mit Wunde; Anschwellung in
# unterschenkelgegend:  Wunde; Anschwellung in der linken Unterschenkelgegend. Haut und sichtbare Schleimhäute mässig durchblutet und kein
# unterschenkelknochen:  gutem Ernährungszustand. Fraktur am linken Unterschenkelknochen mit Wunde; Anschwellung in der linken Unterschenkelgegend. Haut

# Grabbing context sentences from input file..

# Heteronyms (multiple pronunciations based on context)

# are:  Kleinsorge, still bewildered, managed to ask, “Where are the rest?” Just then, the two
# are:  his wife; he simply said, “Oh, you are safe.” She told him that she
# are:  others, who are alive.” The punt was heavy, but he managed to slide it
# are:  he shouted, “All the young men who are not badly hurt come with me!”
# are:  abnormally large, and someone shouted, “The Americans are dropping gasoline. They’re going to set
# are:  III—Details Are Being Investigated
# are:  A woman’s voice stood out especially: “There are people here about to be drowned!
# are:  keep consciously repeating to himself, “These are human beings.” It took him three trips
# are:  of bomb was used. The details are being investigated.” Nor is it probable that
# are:  not come to Asano Park? You are badly needed there.”
# are:  “But there are many dying on the riverbank over
# are:  “Why—when there are many who are heavily wounded on the
# are:  “Yes, we’re all right. My sisters are vomiting, but I’m fine.”
# are:  and said in a kindly voice, “These are tea leaves. Chew them, young man,
# are:  lines and so forth are in operation.”
# are:  a thousand years in Thy sight are but as yesterday when it is past,
# are:  his own voice in person. We are thoroughly satisfied in such a great sacrifice.’
# are:  tiles (“Sister, where are you?” or “All safe and we live at Toyosaka”); naked
# are:  with petechiae, which are hemorrhages about the size of grains of rice, or even
# are:  and south with Lauritsen electroscopes, which are sensitive to both beta rays and gamma
# are:  fortunate that we are Japanese! It was my first time I ever tasted such
# are:  Dr. Sasaki once said, “that they are holding a trial for war criminals in
# august:  August 23, 1946
# august:  minutes past eight in the morning, on August 6, 1945, Japanese time, at the
# august:  Early that day, August 7th, the Japanese radio broadcast for
# august:  water. On the third day, August 8th, some friends who supposed she was dead
# august:  That day, August 8th, Father Cieslik went into the
# august:  Before dawn on August 8th, someone entered the room at
# august:  On August 9th, Father Kleinsorge was still tired.
# august:  after eleven o’clock on the morning of August 9th, the second atomic bomb was
# august:  On August 9th, Mr. Tanimoto was still working
# august:  each meal they were offered. On August 10th, a friend, Mrs. Osaki, came to
# august:  On August 10th, Father Kleinsorge, having heard from
# august:  in the park, Mr. Tanimoto returned, on August 11th, to his parsonage and dug
# august:  On August 11th, word came to the Ninoshima
# august:  assertion on August 12th: “There is nothing to do but admit the tremendous power
# august:  On August 12th, the Nakamuras, all of them
# august:  In Kabe, on the morning of August 15th, ten-year-old Toshio Nakamura heard an
# august:  On August 18th, twelve days after the bomb
# august:  As she dressed on the morning of August 20th, in the home of her
# august:  ship, was taken at the end of August to an engineering school, also at
# august:  lingering radiation at Hiroshima, and in mid-August, not many days after President Truman’s disclosure
# august:  in early August, she was still considering the two alternatives he suggested—taking work as
# august:  out, and early in August, almost exactly on the anniversary of the bombing, he
# bow:  water with a bow and drunk quietly and, spilling any remnant, gave back a
# bowed:  off. Almost all had their heads bowed, looked straight ahead, were silent, and showed
# bowed:  and then raised themselves a little and bowed to him, in thanks.
# close:  things from his church, in the close-packed residential district called Nagaragawa, to a house
# close:  as often happened, he would have been close to the center at the time
# close:  been a close friend. “Where is Fukai-san?” he asked.
# close:  longer keep their footing. Dr. Fujii went close to the shore, crouched down, and
# close:  moved Father Schiffer and Father LaSalle close to the edge of the river and
# close:  who was sitting close by the river, down the embankment at a shallow, rocky
# close:  field, where the many dead lay close and intimate with those who were still
# conflict:  would hold that it would conflict with his duties at the Red Cross Hospital.
# console:  pushcart himself, but the organ console and an upright piano required some aid. A
# console:  often and patted it, as if to console it.
# content:  of the people most concerned with its content, the survivors in Hiroshima, happened to
# converse:  sleep at all; neither did she converse with her sleepless companions.
# do:  Association, and asked him what she should do. He said that she should remain
# do:  and a manservant. He had little to do and did not mind, for he
# do:  Schiffer retired to his room to do some writing. Father Cieslik sat in his
# do:  bomb fell. There was extra housework to do. Her eleven-month-old brother, Akio, had come
# do:  named Machii, and asked in bewilderment, “What do you think it was?”
# do:  burns on their faces and arms. “Why do you suppose it is?” Dr. Fujii
# do:  decided that all he could hope to do was to stop people from bleeding
# do:  his hands. “I can’t do anything,” he said. Father Kleinsorge bound more bandage around
# do:  worst burns. That was all they could do. After dark, they worked by the
# do:  himself. He didn’t know what to do; he had promised some of the dying
# do:  no equipment with which to do the job. She fainted again. When she recovered
# do:  nothing to do but admit the tremendous power of this inhuman bomb.” Already, Japanese
# do:  weeks, but he was not able to do much more than swathe cuts and
# do:  foot.
# do:  wealth; they seemed to be able to do anything they wanted. He had nothing
# do:  hard—but what could he do? By July, he was worn out, and early in
# do:  her. There was nothing for her to do except read and look out, from
# do:  capable of the work he once could do; Dr. Fujii had lost the thirty-room
# do:  fire. His son said, ‘Father, we can do nothing except make our mind up
# does:  even when it serves a just purpose. Does it not have material and spiritual
# drawer:  and shifted papers. She thought that before she began to make entries in her
# house:  watching a neighbor tearing down his house because it lay in the path of
# house:  district called Nagaragawa, to a house that belonged to a rayon manufacturer in Koi,
# house:  morning, Mr. Tanimoto started for Mr. Matsuo’s house. There he found that their burden
# house:  the front steps into the house and dived among the bedrolls and buried himself
# house:  head and saw that the rayon man’s house had collapsed. He thought a bomb
# house:  arose, dressed quickly, and hurried to the house of Mr. Nakamoto, the head of
# house:  She had taken a single step (the house was 1,350 yards, or three-quarters of
# house:  bomb was dropped to see a house guest off on a train. He rose
# house:  living in the mission house; Mr. Fukai, the secretary of the diocese; Mrs. Murata,
# house:  knew how he got out of the house. The next things he was conscious
# house:  had been safely cushioned within the falling house by the bedding stored in the
# house:  up from under the ruins of her house after the explosion, and seeing Myeko,
# house:  Why did our house fall down? What happened?” Mrs. Nakamura, who did not know
# house:  was the Jesuit mission house, alongside the Catholic kindergarten to which Mrs. Nakamura had
# house:  other priests living in the mission house appeared—Father Cieslik, unhurt, supporting Father Schiffer, who
# house:  were buried under the ruins of their house, which was at the back of
# house:  public bath next door to the mission house had caught fire, but since there
# house:  came back and said that Dr. Kanda’s house was ruined and that fire blocked
# house:  he finished, he ran into the mission house again and found the jacket of
# house:  know exactly which part of the house he is under?” he asked.
# house:  They went around to the house, the remains of which blazed violently,
# house:  on the second floor of the mission house, facing in the direction of the
# house:  and wires. From every second or third house came the voices of people buried
# house:  in the crushed shell of a house, and he began carrying water to the
# house:  bomb blew down his house, and a joist pinned him by the legs, in
# house:  he decided to go to his parental house, in the suburb of Nagatsuka. He
# house:  Dr. Fujii reached his family’s house in the evening. It was five
# house:  had been living at the mission house—had arrived at the Novitiate, in the hills
# house:  on the floor of his family’s roofless house on the edge of the city.
# house:  biscuits and rice balls, but the charnel-house smell was so strong that few were
# house:  he soon found one beside an empty house and wheeled it back. The priests
# house:  the plumbing of a vanished house—and he filled his vessels and returned. When he
# house:  been to the site of the mission house in the city and had retrieved
# house:  rooming with Mr. Fukai at the mission house, told the priests that the secretary
# house:  while in the ruins of the mission house, but he found nothing. He went
# house:  had buried her under their house with the baby strapped to her back, and
# house:  he had eventually gone to the summer house of a friend of his named
# house:  place of worship in a private house he had rented in the outskirts—Mr. Tanimoto
# house:  Now he was living in the summer house of Mr. Okuma, in Fukawa. This
# house:  eventually it made its way to the house in Kabe where Mrs. Nakamura lay
# house:  flood, Dr. Fujii lived in the peasant’s house on the mountain above the Ota.
# house:  site of her former house, and though its floor was dirt and it was
# house:  over the roof of the badly damaged house he had rented in Ushida. The
# house:  to build a three-story mission house exactly like the one that had been destroyed
# house:  except read and look out, from her house on a hillside in Koi, across
# house:  buried under the house, because I had to take care of my mother who
# house:  by the bomb under the two storied house with his son, a student of
# minute:  the air-raid siren went off—a minute-long blast that warned of approaching planes but indicated
# minute:  a forty-five-minute trip to the tin works, in the section of town called Kannon-machi.
# number:  unoccupied estate to a large number of his friends and acquaintances, so that they
# number:  and when she thought of the number of trips they had made in past
# number:  a month because in July, as the number of untouched cities in Japan dwindled
# number:  see enough to be amazed at the number of houses that were down all
# number:  Many people were vomiting. A tremendous number of schoolgirls—some of those who had been
# number:  her. He pulled away a great number of books, until he had made a
# number:  in the streets, but a great number sat and lay on the pavement, vomited,
# number:  his boat, he saw that a great number of people had moved toward the
# number:  get under it. A great number of people, even badly burned ones, crawled into
# number:  of the still-burning fires, a number of wounded people lying at the edge of
# number:  must have drowned. He saw a number of bodies floating in the river.
# number:  the Ninoshima Military Hospital that a large number of military casualties from the Chugoku
# number:  in the number of white blood corpuscles reduced the patient’s capacity to resist infection,
# number:  Zempoji Temple in Koi rose into the thousands, the statisticians began to say that
# number:  a carpenter from Kabe was building a number of wooden shanties in Hiroshima which
# number:  A surprising number of the people of Hiroshima remained
# permit:  on his own, and without a permit, he had begun visiting a few sick
# present:  decided to effect a settlement of the present situation by resorting to an extraordinary
# present:  matter is whether total war in its present form is justifiable, even when it
# record:  her and put down on her record card, in the correct, scrunched-up German in
# relay:  where they had arranged to meet a relay of other priests, left him with
# resume:  and resume the work of a seamstress.
# row:  the row of dowdy banks, caricaturing a shaken economic system); and in the streets
# sake:  with friends, always sensibly and for the sake of conversation. Before the war, he
# sake:  our country’s sake.’ Thus they pledged to me, even women and children did the
# sake:  bombing, believing that it was for Emperor’s sake.”
# subject:  newspapers were being extremely cautious on the subject of the strange weapon.
# subject:  States printed and mimeographed and bound into little books. The Americans knew of the
# tear:  where blood is manufactured, and gradually tear it down. Whatever its source, the disease
# wind:  had caught fire, but since there the wind was southerly, the priests thought their
# wind:  which way; here on the bridge the wind was easterly. New fires were leaping
# wind:  all around were burning, and the wind was now blowing hard. “Do you know
# wind:  was coming closer on the wind, which had swung around and was now from
# wind:  avoid the heat of the fire, the wind grew stronger and stronger, and soon,
# wind:  water, and as they fell, the wind grew stronger and stronger, and suddenly—probably because
# wound:  out by it. A mosquito net was wound intricately, as if it had been
# wound:  Sasaki was incapable of dressing another wound. He and some other survivors of the
# wound:  one of them touched her wound, she fainted. She came to in time to
# wound:  the sun. Pus oozed out of her wound, and soon the whole pillow was
# wound:  were normal and the infection in the wound was beginning to clear up. On
# wound:  got a deep wound on her eye and our house soon set fire and
# allied:  of supplies and instruments hampered them. Allied doctors who came in after the surrender
# allied:  A new municipal government, set up under Allied Military Government direction, had gone to
# allied:  the Allied occupation forces, or borrowing from her relatives enough money, about five hundred
# compound:  living in the mission compound, which was in the Nobori-cho section—Father Superior LaSalle and
# compound:  retired across the compound to the bigger building. There, in his room on the
# compound:  men went out of the compound and up the street.
# compound:  was at the back of the Jesuit compound, and at the same time the
# compound:  went back to the Catholic compound and told the Father Superior that the fire
# compound:  did have a fairly ugly compound fracture. He said quite coldly that he was
# compound:  just to have another look at the wreckage, and then started back to the
# compound:  still prevented the proper setting of the compound fracture of her lower left leg.
# compound:  she had a compound fracture of the left tibia, with swelling of the left
# compound:  in the fire. In the compound, carpenters cut timbers, gouged mortises, shaped tenons, whittled
# defense:  the path of an air-raid-defense fire lane; Father Wilhelm Kleinsorge, a German priest of
# defense:  organizing air-raid defense for about twenty families.
# defense:  Neighborhood Association, came across the street with her head all bloody, and said that
# entrance:  and was red all over. Near the entrance to the park, an Army doctor
# intimate:  the many dead lay close and intimate with those who were still living, and
# learned:  death at Singapore.” She learned later that he had died on February 15th, the
# learned:  four hours’ commuting. He had recently learned that the penalty for practicing without a
# learned:  he had made the afternoon before. He learned that their name was Kataoka; the
# learned:  hunting for the children’s family. First, he learned through the police that an uncle
# learned:  what she had seen and learned in the city that she could not speak
# learned:  some far more important facts about the nature of the bomb. General MacArthur’s headquarters
# live:  go and live there with him, to cook for him, bathe, massage, and read
# live:  inflammable wreckage falling on cookstoves and live wires), Mrs. Nakamura suggested going over to
# live:  came into contact with the live wires of the city power system. “That means,”
# live:  and we live at Toyosaka”); naked trees and canted telephone poles; the few standing,
# progress:  it was after dark, and progress was made extremely difficult by the tangle of
# progress:  Here his injuries seemed to make good progress, and he even began to treat
# putting:  he came to them. Other doctors were putting compresses of saline solution on the
# putting:  Some returning residents were putting up their own shanties and huts, and planting small
# read:  Fujii was settling down cross-legged to read the Osaka Asahi on the porch of
# read:  cook, and sat down to read that morning’s Hiroshima Chugoku. To her relief, the
# read:  went out on the porch to read the paper. This porch—in fact, the whole
# read:  the Osaka Asahi. He liked to read the Osaka news because his wife was
# read:  of his sickness—he began to read Mass in the mission chapel, a small Japanese-style
# read:  stomach to ease his pain, and read. Father Superior LaSalle stood at the window
# read:  reminded him of something he had read as a boy about a large meteor
# read:  Read classic New Yorker stories, curated by
# read:  shelter stairway to get light, Mr. Tanimoto read loudly from a Japanese-language pocket Bible:
# read:  Mr. Tanaka died as Mr. Tanimoto read the psalm.
# read:  of de Maupassant, and she tried to read the stories, but she could concentrate
# read:  more tired. In June, he read an article in the Hiroshima Chugoku warning survivors
# read:  was nothing for her to do except read and look out, from her house
# root:  as genshi bakudan—the root characters of which can be translated as “original child bomb.”
# second:  was standing in his window on the second floor of the mission house, facing
# second:  fallen telephone poles and wires. From every second or third house came the voices
# second:  water, he made a second trip. This time, the woman by the bridge was
# second:  with only one hour’s sleep. On the second day, he began to sew up
# second:  on the morning of August 9th, the second atomic bomb was dropped, on Nagasaki.
# second:  began smelling bad on the second day. Once, Mr. Tanimoto sat with her for
# second:  and around the hospital. Beginning on the second day, whenever a patient appeared to
# second:  whole handful of hair; the second time, the same thing happened, so she stopped
# second:  radiation or nervous shock. The second stage set in ten or fifteen days after
# second:  Miss Sasaki herself brought it up the second time he dropped in on her.
# shower:  around her as she landed, and a shower of tiles pommelled her; everything became
# sin:  He has fallen from grace through sin.” And he went on to explain all
# supposed:  comprised a reconnaissance.) Pushing the handcart up to the rayon man’s house was tiring,
# supposed:  them from getting out of what they supposed to be the local circle of
# supposed:  August 8th, some friends who supposed she was dead came to look for her
# use:  that had previously been designated for use as a temporary hospital in case of
# use:  I must use it for others, who are alive.” The punt was heavy, but
# use:  in the use of atomic power, which (as the voices on the short wave
# use:  of their experiences and of the use of the atomic bomb was, of course,
# use:  As for the use of the bomb, she would say, “It was war and
# use:  try the men who decided to use the bomb and they should hang them
# use:  as poison gas and were against its use on a civilian population. Others were.'''

# chunks = chunk_text_to_lists(100, text)
# print(chunks)