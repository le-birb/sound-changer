
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