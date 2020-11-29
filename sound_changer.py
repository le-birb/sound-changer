
import io




if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()

    parser.add_argument("lex_file", action = "store", type = argparse.FileType("r", encoding = "utf-8"))
    parser.add_argument("rules_file", action = "store", type = argparse.FileType("r", encoding = "utf-8"))
    parser.add_argument("-o", "--out", action = "store", type = argparse.FileType("w", encoding = "utf-8"),\
        dest = "out_file", default = None)
    parser.add_argument("-c", "--classes", action = "store", type = argparse.FileType("r", encoding = "utf-8"),\
        dest = "phon_classes_file", default = None)

    args = parser.parse_args()

    line_count = 0
    group_definition = False
    rule_list = []
    curr_group = []

    for line in args.rules_file:
        line = line.strip()
        line_count = line_count + 1
        
        if line == "":
            continue # skip empty line
        elif line.startswith("%"):
            continue # skip comment
        
        elif line.startswith("group:"):
            group_definition = True
            last_group_def = line_count
            continue
        elif line.startswith("end group"):
            group_definition = False
            continue

        else:
            # parse rule, add to curr_group
            pass

            # evaluate only after each rule group is over
            # individual rules will count as a group
            if not group_definition:
                rule_list.append(curr_group)

    if group_definition:
        # error for unfinished group rule at last_group_def
        pass
    
    # here is where rules will be applied to words




# when evaluating a rule on a word
# find places where any pre-env matches
# also keep track of any neg envs that match here
# for each one:
    # test for the target sound(s)
    # if found:
        # test the corresponding post-envs, including negatives
        # itertools.compress will likely be useful here
        # if any env and no neg-envs match:
            # make the replacement
            # behavior from here will depend on the mode used eventually