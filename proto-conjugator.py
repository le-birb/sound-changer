
import argparse

endings = ['re', 'ta', 'tu', 'te', 'rim', 'ri']

if __name__ == '__main__':

    parser = argparse.ArgumentParser()

    parser.add_argument("verb_file", action = "store", type = argparse.FileType("r", encoding = "utf-8"))
    parser.add_argument("-o", "--out", action = "store", type = argparse.FileType("w", encoding = "utf-8"), dest = "out_file", default = None)

    args = parser.parse_args()

    conjugated_list = []

    for line in args.verb_file:
        if line == "\n":
            continue

        verb = line.strip()

        conjugated_list.append(verb)

        for ending in endings:
            conjugated_list.append(verb + ending)
        
        conjugated_list.append('')


    if not args.out_file:
        out_file = open("./conjugateds", "w")

    args.out_file.write("\n".join(word for word in conjugated_list))


