import tkinter as tk
from tkinter import *
from tkinter import messagebox


class App(Frame):

    def __init__(self,parent):
        Frame.__init__(self,parent)
        self.parent = parent
        self.initUI()

    def initUI(self):

        self.pack()
        info = Label(self, text=" Sifrelemek veya cözmek istediginiz metni asagiya giriniz",)
        info.grid(row= 0 , column=0)

        self.textbox = Text(self,width=50,height=12)
        self.textbox.grid(row=1,)

        self.returns = Label(self, text=" SONUC ",)
        self.returns.grid(row= 2 , )

        self.result_textbox = Text(self,width=50,height=12)
        self.result_textbox.grid(row=3,)

        self.encryptButton = Button(self,text= " Sifrele", command= self.encrypt, width= 10,relief=SUNKEN) 
        self.encryptButton.grid(row=4,sticky=E)

        self.decryptButton = Button(self,text= " Cöz", command= self.decrypt, width=10,relief=SUNKEN) 
        self.decryptButton.grid(row=4,sticky=W)        

        self.pack()

    def get_message(self):
        msg = self.textbox.get(1.0, "end-1c")
        return msg 
    
    def encrypt(self):
        msg = self.get_message()
        letters = []
        for letter in msg:
            if ('a' <= letter <= 'z' or 'A' <= letter <= 'Z'):
                letters.append(letter)
            elif(letter == ' '):
                letters.append(" ")

        encrypted = []
        for letter in letters:
            if ('a' <= letter <= 'z' or 'A' <= letter <= 'Z'):
                tmp = ord(letter)
                new = chr(tmp+3)
                encrypted.append(new)
            elif( letter == " "):
                encrypted.append(" ")

        new_msg = ""
        for letter in encrypted:
            if ('a' <= letter <= 'z' or 'A' <= letter <= 'Z'):
                new_msg += letter
            elif (letter == " "):
                new_msg += " "

        self.result_textbox.insert(END,new_msg)

    def decrypt(self):
        
        msg = self.get_message()
        letters = []
        for letter in msg:
            if ('a' <= letter <= 'z' or 'A' <= letter <= 'Z'):
                letters.append(letter)
            elif(letter == ' '):
                letters.append(" ")

        decrypted = []
        for letter in letters:
            if ('a' <= letter <= 'z' or 'A' <= letter <= 'Z'):
                tmp = ord(letter)
                new = chr(tmp-3)
                decrypted.append(new)
            elif( letter == " "):
                decrypted.append(" ")

        new_msg = ""
        for letter in decrypted:
            if ('a' <= letter <= 'z' or 'A' <= letter <= 'Z'):
                new_msg += letter
            elif (letter == " "):
                new_msg += " "

        self.result_textbox.insert(END,new_msg)


def main():
    root = Tk()
    root.title("Sifreleme Uygulamasi")
    cryptologyApp = App(root)
    cryptologyApp.mainloop()

main()