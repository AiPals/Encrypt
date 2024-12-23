from cryptography.fernet import Fernet
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import os
import base64
import getpass
from stegano import lsb
def generate_key(password):
    """Derive a key from a password using PBKDF2."""
    salt = os.urandom(32)
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA512(),
        length=32,
        salt=salt,
        iterations=10000000, 
        backend=default_backend()
    )
    key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
    return key, salt
def hide_salt_in_image(salt, image_path):
    """Hide the salt inside the image itself and overwrite the original image."""
    salt_str = base64.b64encode(salt).decode()  # Convert the salt to a base64-encoded string
    secret_image = lsb.hide(image_path, salt_str)  # Hide the salt in the image
    temp_output = image_path + "_temp.png"
    secret_image.save(temp_output)
    os.remove(image_path)  # Delete the original image
    os.rename(temp_output, image_path)  # Rename the temp image to the original name
    print(f"Salt has been hidden inside '{image_path}' and original image has been overwritten.")
def extract_salt_from_image(image_path):
    """Extract the salt from an image."""
    hidden_salt_str = lsb.reveal(image_path)
    if hidden_salt_str:
        return base64.b64decode(hidden_salt_str)  # Convert the string back to bytes
    else:
        raise ValueError("No salt found in the image.")
def encrypt_file(filename, key):
    """Encrypt a file using the given key."""
    fernet = Fernet(key)
    with open(filename, "rb") as file:
        file_data = file.read()
    encrypted_data = fernet.encrypt(file_data)
    with open(filename, "wb") as file:
        file.write(encrypted_data)
    print(f"File '{filename}' has been encrypted.")
def decrypt_file(filename, key):
    """Decrypt a file using the given key."""
    fernet = Fernet(key)
    with open(filename, "rb") as file:
        encrypted_data = file.read()
    decrypted_data = fernet.decrypt(encrypted_data)
    with open(filename, "wb") as file:
        file.write(decrypted_data)
    print(f"File '{filename}' has been decrypted.")
def main():
    choice = input("Do you want to (e)ncrypt or (d)ecrypt a file? ").lower()
    password = getpass.getpass("Enter your password: ")
    if choice == 'e':
        key, salt = generate_key(password)
        filename = input("Enter the filename to encrypt: ")
        image_path = input("Enter the image path to hide the salt: ")
        encrypt_file(filename, key)  
        hide_salt_in_image(salt, image_path)  
        print(f"Encrypted file and hidden salt inside '{image_path}'")
    elif choice == 'd':
        image_path = input("Enter the image path to extract the salt: ")
        salt = extract_salt_from_image(image_path)
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA512(),
            length=32,
            salt=salt,
            iterations=10000000, 
            backend=default_backend()
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        filename = input("Enter the filename to decrypt: ")
        decrypt_file(filename, key)
    else:
        print("Invalid choice. Please enter 'e' or 'd'.")
if __name__ == "__main__":
    main()