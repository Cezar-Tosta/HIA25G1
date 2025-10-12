from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

new_password = "prevensus"  # or your new password
hashed_password = pwd_context.hash(new_password)
print("New hashed password:", hashed_password)