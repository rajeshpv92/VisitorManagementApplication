from werkzeug.security import generate_password_hash

def hash_password(password):
    # Hash the password using SHA-256 or another algorithm of your choice
    return generate_password_hash(password)
