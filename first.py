lang={
    "kala" :"black",
    "safed":"white",
    "hara":"green"
}
word = input("Enter a word of which you want to understand the meaning of: ")
k = lang[word]
import pyttsx3
engine = pyttsx3.init()
engine.say(k)
print(k)
engine.runAndWait()