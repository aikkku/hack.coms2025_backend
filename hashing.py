import bcrypt

class Hash():
    @staticmethod
    def bcrypt(password: str) -> str:
        # Convert password to bytes and hash it
        password_bytes = password.encode('utf-8')
        # Generate salt and hash password
        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw(password_bytes, salt)
        # Return as string (bcrypt hash includes salt)
        return hashed_password.decode('utf-8')
    
    @staticmethod
    def verify(plain_password: str, hashed_password: str) -> bool:
        # Convert both to bytes
        password_bytes = plain_password.encode('utf-8')
        hashed_bytes = hashed_password.encode('utf-8')
        # Verify password
        return bcrypt.checkpw(password_bytes, hashed_bytes)