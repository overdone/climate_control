def str_rjust(s, length, char):
    if char is None or len(char) != 1 or length < len(s):
        return s

    return (char * (length - len(s))) + s


def str_reverse(s):
    return ''.join(reversed(s))
