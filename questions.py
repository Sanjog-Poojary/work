
def rem(l, word):
    for item in l:
        l.remove(word)
        return l

l =["Harry", "Rohan","Shubham", "an"]
print(l)
var = input("Please enter the word you don't want:")
print(rem(l, var))