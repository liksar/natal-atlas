import unicodedata

def normalize(value):
    return unicodedata.normalize('NFKC', value).casefold()
