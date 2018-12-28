def getKey(f):
    with open(f, 'r') as key:
        for line in key:
            return line
