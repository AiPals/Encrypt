import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from cryptography.fernet import Fernet
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import os
import base64
from stegano import lsb


def generate_key(password):
    salt = os.urandom(32)
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA512(),
        length=32,
        salt=salt,
        iterations=100000,
        backend=default_backend()
    )
    key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
    return key, salt


def hide_salt_in_image(salt, image_path):
    salt_str = base64.b64encode(salt).decode()
    secret_image = lsb.hide(image_path, salt_str)
    temp_output = image_path + "_temp.png"
    secret_image.save(temp_output)
    os.remove(image_path)
    os.rename(temp_output, image_path)


def extract_salt_from_image(image_path):
    hidden_salt_str = lsb.reveal(image_path)
    if hidden_salt_str:
        return base64.b64decode(hidden_salt_str)
    else:
        raise ValueError("No salt found in the image.")


def encrypt_file(filename, key, progress_bar, percentage_label):
    fernet = Fernet(key)
    file_size = os.path.getsize(filename)
    chunk_size = 1024 * 1024
    encrypted_chunks = []
    with open(filename, "rb") as file:
        total_read = 0
        while chunk := file.read(chunk_size):
            encrypted_chunk = fernet.encrypt(chunk)
            encrypted_chunks.append(encrypted_chunk)
            total_read += len(chunk)
            progress = int((total_read / file_size) * 100)
            update_progress(progress_bar, percentage_label, progress)
    with open(filename, "wb") as file:
        for chunk in encrypted_chunks:
            file.write(chunk)


def decrypt_file(filename, key, progress_bar, percentage_label):
    fernet = Fernet(key)
    file_size = os.path.getsize(filename)
    chunk_size = 1024 * 1024
    decrypted_chunks = []
    with open(filename, "rb") as file:
        total_read = 0
        while chunk := file.read(chunk_size):
            decrypted_chunk = fernet.decrypt(chunk)
            decrypted_chunks.append(decrypted_chunk)
            total_read += len(chunk)
            progress = int((total_read / file_size) * 100)
            update_progress(progress_bar, percentage_label, progress)
    with open(filename, "wb") as file:
        for chunk in decrypted_chunks:
            file.write(chunk)


def update_progress(progress_bar, percentage_label, value):
    progress_bar["value"] = value
    percentage_label.config(text=f"{value}%")
    root.update()


def show_progress(task_name, determinate=False):
    clear_window(exclude_widgets=[password_entry])
    label = tk.Label(root, text=f"{task_name} in progress...", font=("Arial", 12), bg="#f0f4f7", fg="#333")
    label.pack(pady=20)
    progress_bar = ttk.Progressbar(root, mode='determinate' if determinate else 'indeterminate', length=250)
    progress_bar.pack(pady=10)
    percentage_label = tk.Label(root, text="0%", font=("Arial", 10), bg="#f0f4f7")
    percentage_label.pack(pady=5)
    if not determinate:
        progress_bar.start()
    root.update()
    return progress_bar, percentage_label


def close_progress(progress_bar):
    progress_bar.stop()
    show_main_menu()


def encrypt_action(password):
    key, salt = generate_key(password)
    filepath = filedialog.askopenfilename(title="Select File to Encrypt")
    if not filepath:
        return
    image_path = filedialog.askopenfilename(title="Select Image to Hide Salt")
    if not image_path:
        return
    progress_bar, percentage_label = show_progress("Encrypting", determinate=True)
    try:
        encrypt_file(filepath, key, progress_bar, percentage_label)
        hide_salt_in_image(salt, image_path)
        messagebox.showinfo("Success", f"File '{filepath}' has been encrypted.")
    except Exception as e:
        messagebox.showerror("Error", f"An error occurred: {e}")
    finally:
        close_progress(progress_bar)


def decrypt_action(password):
    image_path = filedialog.askopenfilename(title="Select Image with Hidden Salt")
    if not image_path:
        return
    try:
        salt = extract_salt_from_image(image_path)
    except ValueError as e:
        messagebox.showerror("Error", str(e))
        show_main_menu()
        return
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA512(),
        length=32,
        salt=salt,
        iterations=100000,
        backend=default_backend()
    )
    key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
    filepath = filedialog.askopenfilename(title="Select File to Decrypt")
    if not filepath:
        return
    progress_bar, percentage_label = show_progress("Decrypting", determinate=True)
    try:
        decrypt_file(filepath, key, progress_bar, percentage_label)
        messagebox.showinfo("Success", f"File '{filepath}' has been decrypted.")
    except Exception as e:
        messagebox.showerror("Error", f"An error occurred: {e}")
    finally:
        close_progress(progress_bar)


def show_main_menu():
    clear_window()
    root.title("Encrypt Tool")
    label = tk.Label(root, text="Encrypt or Decrypt Files", font=("Arial", 18, "bold"), bg="#f0f4f7", fg="#333")
    label.pack(pady=20)

    button_frame = tk.Frame(root, bg="#f0f4f7")
    button_frame.pack(pady=10)

    encrypt_button = ttk.Button(button_frame, text="Encrypt", command=encrypt_choice)
    encrypt_button.grid(row=0, column=0, padx=15, pady=10)

    decrypt_button = ttk.Button(button_frame, text="Decrypt", command=decrypt_choice)
    decrypt_button.grid(row=0, column=1, padx=15, pady=10)


def encrypt_choice():
    show_password_input(encrypt_action)


def decrypt_choice():
    show_password_input(decrypt_action)


def show_password_input(action_function):
    clear_window()
    root.configure(bg="#f0f4f7")

    label = tk.Label(root, text="Enter Password", font=("Arial", 14), bg="#f0f4f7", fg="#333")
    label.pack(pady=(30, 10))

    global password_entry
    password_entry = ttk.Entry(root, show="*", font=("Arial", 12), width=25)
    password_entry.pack(pady=10)

    submit_button = ttk.Button(root, text="Submit", command=lambda: submit_password(action_function))
    submit_button.pack(pady=20)


def submit_password(action_function):
    password = password_entry.get()
    if password:
        action_function(password)
    else:
        messagebox.showwarning("Input Required", "Please enter a password.")


def clear_window(exclude_widgets=None):
    if exclude_widgets is None:
        exclude_widgets = []
    for widget in root.winfo_children():
        if widget not in exclude_widgets:
            widget.destroy()


def main():
    global root
    root = tk.Tk()
    root.title("Encrypt Tool")
    root.geometry("400x200")
    root.configure(bg="#f0f4f7")

    icon_image = tk.PhotoImage(file="Encrypt.png")
    root.iconphoto(True, icon_image)

    style = ttk.Style(root)
    style.theme_use("clam")

    show_main_menu()
    root.mainloop()


if __name__ == "__main__":
    main()
