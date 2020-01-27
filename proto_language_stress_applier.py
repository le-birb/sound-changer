
import argparse
import re

parser = argparse.ArgumentParser()

parser.add_argument("input_file", action = "store", type = argparse.FileType("r", encoding = "utf-8"))
parser.add_argument("output_file", action = "store", type = argparse.FileType("w", encoding = "utf-8"))

args = parser.parse_args()

#
# takes a list of proto-talossian words from a file and adds a ' before the stressed vowels
#

def add_stress(syllable:str) -> str:
    return re.sub(r"([aeiou])", r"'\1", syllable)

def is_strong(syllable: str) -> bool:
    return re.search(r"^t[sś]", syllable) or re.search(r"[nm]$", syllable)

stressed_words = []

for word in args.input_file:

    # get rid of the trailing newline
    word = word.strip()

    # skip invalid words
    if word == "#N/A" or word == "":
        continue

    syllable_list = []

    while word != "":
        
        # grab the last syllable
        syllable_list.append(re.search(pattern = r"(t[sś]|[^\s\d])[aeiou][nm]?$", string = word).group())

        word = word[:-len(syllable_list[-1])]
    
    # reverse because the syllables were added backwards
    syllable_list.reverse()

    stressed_syllable = 0

    # apply primary stress
    for i in range(len(syllable_list)):

        # find the first syllable with either an affricate or a coda nasal
        if is_strong(syllable_list[i]):
            syllable_list[i] = add_stress(syllable_list[i])
            stressed_syllable = i
            break

    else:
        syllable_list[0] = add_stress(syllable_list[0])

    last_stressed = True
    stress_next = False

    # apply secondary stress, first propogating towards the beginning of the word
    for i in range(stressed_syllable - 1, -1, -1):
        
        # no consecutive stress
        if last_stressed:
            last_stressed = False
            continue
        
        # always stress the third syllable
        elif stress_next:
            syllable_list[i] = add_stress(syllable_list[i])
            stress_next = False
            last_stressed = True
            continue

        # the second syllable is stressed if it is strong, else it is unstressed and the next is stressed
        else:
            if is_strong(syllable_list[i]):
                syllable_list[i] = add_stress(syllable_list[i])
                last_stressed = True

            else:
                stress_next = True
            
            continue

    
    # now do the same thing in the other direciton
    last_stressed = True
    stress_next = False

    # apply secondary stress, first propogating towards the beginning of the word
    for i in range(stressed_syllable + 1, len(syllable_list)):
        
        # no consecutive stress
        if last_stressed:
            last_stressed = False
            continue
        
        # always stress the third syllable
        elif stress_next:
            syllable_list[i] = add_stress(syllable_list[i])
            stress_next = False
            last_stressed = True
            continue

        # the second syllable is stressed if it is strong, else it is unstressed and the next is stressed
        else:
            if is_strong(syllable_list[i]):
                syllable_list[i] = add_stress(syllable_list[i])
                last_stressed = True

            else:
                stress_next = True
            
            continue

    stressed_words.append("".join(syllable_list))

args.output_file.write("\n".join(stressed_words))
