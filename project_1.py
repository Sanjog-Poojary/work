import random
computer = random.choice([-1,0,1])
your_choice = input("Enter your choice: ")
youDict = {"s":1, "w":-1, "g":0}
reverseDict = {1:"Snake", 0:"Gun", -1:"Water"}

you = youDict[your_choice]
print(f"you choose {reverseDict[you]}\nComputer choose {reverseDict[computer]}")

if(you == computer):
    print("It is a draw!")
else:
    if(computer==1 and you ==-1):
        print("You lose.")
    elif(computer==1 and you ==0):
        print("You win!!!")
    elif(computer==0 and you== 1):
        print("You lose.")
    elif(computer==0 and you==-1):
        print("You win!!!")
    elif(computer==-1 and you==1):
        print("You win!!!")
    elif(computer==-1 and you==0):
        print("you lose.")
    else:
        print("There might be an error.")
