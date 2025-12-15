import tkinter as tk
from gui import CryptographyApp

def main():
    root = tk.Tk()
    app = CryptographyApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()