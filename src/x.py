import sys
for line in sys.stdin:
    spaces=-2
    for word in line.split(","):
        buff=""
        if "(" in word:
            spaces+=2
            buff+="\n"+" "*spaces
        buff+=word
        if ")" in word:
            buff+="\n"
            spaces-=2
        else:
            buff+=","
        sys.stdout.write(buff)