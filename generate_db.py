from chat_server import db

def generate_database():
    db.create_all()


def drop_database():
    db.drop_all()


if __name__ == "__main__":
    generate_database()
