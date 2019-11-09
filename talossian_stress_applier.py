
import argparse
import re

parser = argparse.ArgumentParser()

parser.add_argument("input_file", action = "store", type = argparse.FileType("r", encoding = "utf-8"))
parser.add_argument("output_file", action = "store", type = argparse.FileType("w", encoding = "utf-8"))

args = parser.parse_args()

#
# takes a list of proto-talossian words from a file and adds a ' before the stressed vowels
#

stressed_words = []

for word in args.input_file:

    # get rid of the trailing newline
    word = word.strip()

    # skip invalid words
    if word == "#N/A":
        continue

    syllable_list = []

    while word != "":
        
        # grab the last syllable
        syllable_list.append(re.search(pattern = r"(t[sś]|[^\s\d])[aeiou][nm]?$", string = word).group())

        word = word[:-len(syllable_list[-1])]

    for i in range(len(syllable_list)):

        # find the first syllable with either an affricate or a coda nasal
        if re.search(r"^t[sś]", syllable_list[i]) or re.search(r"[nm]$", syllable_list[i]):
            syllable_list[i] = re.sub(r"([aeiou])", r"'\1", syllable_list[i])
            break

    else:
        syllable_list[0] = re.sub(r"([aeiou])", r"'\1", syllable_list[0])

    stressed_words.append("".join(syllable_list))

args.output_file.write("\n".join(stressed_words))
