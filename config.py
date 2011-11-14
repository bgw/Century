try:
    raw_input
except:
    raw_input = input
import getpass

print("Username?")
username = raw_input()

password = getpass.getpass("Password: ")
