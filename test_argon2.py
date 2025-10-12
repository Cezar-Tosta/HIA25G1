from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

# Hash a password
hashed = pwd_context.hash("test123")
print("Hashed password:", hashed)

# Verify the password
verified = pwd_context.verify("test123", hashed)
print("Verification result:", verified)
