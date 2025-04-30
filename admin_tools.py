import os
from colorama import Fore, Style, init

init()

last_status = None


def set_privilege_level():
    global last_status
    level = input("Enter the privilege level you want to set: ")
    try:
        level = int(level)
    except Exception as e:
        last_status = Fore.RED + f"Error setting privilege level: {e}" + Style.RESET_ALL
        return

    username = input("Enter the username of the user you want to set the privilege level for: ")
    from main import app
    from models import User, db
    try:
        with app.app_context():
            user = User.query.filter_by(user_login=username).first()
            if not user:
                last_status = Fore.RED + f"User not found." + Style.RESET_ALL
                return
            user.user_privilege = int(level)
            db.session.commit()
            last_status = Fore.GREEN + f"Privilege level for {username} set to {level}." + Style.RESET_ALL
    except Exception as e:
        last_status = Fore.RED + f"Error setting privilege level: {e}" + Style.RESET_ALL


def check_selection(selection):
    if int(selection) > len(commands) or int(selection) < 1:
        print("Invalid selection.")
        return False
    return True

def main():

    os.system("cls")
    print(f"Admin Tools\nLast Status:  {last_status}")
    selection = input("\nType a number with what action you want to do: \n1. Create a dummy user\n2. Create a user.\n3. Reset Password\n4. Set Privilege level\n5. Set users points\nX to Exit.\n>")
    if selection.lower() == "x": exit()

    if not check_selection(selection):
        print("Invalid selection.")
        return

    selection = int(selection) - 1
    commands[selection]()


def create_dummy_user():
    import random
    global last_status
    try:
        random_names = "tiger frog spider moose deer".split()
        new_user = f"{random.choice(random_names)}{random.randint(1,999)}"
        email = f"{new_user}@dummy.test"
        password = "password123"
        create_user(new_user, new_user, password, email)
        last_status = Fore.GREEN + f"Created dummy user {new_user} with password: {password}" + Style.RESET_ALL
    except Exception as e:
        last_status = Fore.RED + f"Error creating dummy user: {e}" + Style.RESET_ALL
def create_user_options():
    global last_status
    from main import app
    from models import User, db
    try:
        username = input("Enter a username: ")
        alias = input("Enter an alias: ")
        email = input("Enter an email: ")
        plaintext_pass = input("Enter a password: ")
        user = create_user(username, alias, plaintext_pass, email)


        last_status = Fore.GREEN + f"Created user {user['username']} with id {user['id']}" + Style.RESET_ALL
    except Exception as e:
        last_status = Fore.RED + f"Error creating user: {e}" + Style.RESET_ALL


def create_user(username, alias, plaintext_pass, email):
    from main import app
    from models import User, db
    with app.app_context():
        user = User()
        user.user_login = username
        user.user_alias = alias
        user.password = plaintext_pass
        user.user_email = email
        db.session.add(user)
        db.session.commit()
        return {"username" : username, "id": user.user_id}



def update_points():
    global last_status
    from main import app
    from models import User, db
    try:
        username = input("Enter a username: ")
        points = input("Set the users points: ")
        points = int(points)
        with app.app_context():
            user = User.query.filter_by(user_login=username).first()
            user.user_balance = points
            db.session.commit()
            last_status = Fore.GREEN + f"Updated {user.user_login} points to : {points} points" + Style.RESET_ALL
    except Exception as e:
        last_status = Fore.RED + f"Error setting privilege level: {e}" + Style.RESET_ALL
        return




def set_password():
    global last_status
    from main import app
    from models import User, db
    try:
        username = input("Enter the username of the user you want to reset the password for: ")
        with app.app_context():
            user = User.query.filter_by(user_login=username).first()
            if not user:
                print("User not found.")
                return
            plaintext_pass = input("Enter a new password: ")
            user.password = plaintext_pass
            db.session.commit()
        last_status = Fore.GREEN + f"Password for {username} reset." + Style.RESET_ALL
    except Exception as e:
        last_status = Fore.RED + f"Error resetting password: {e}" + Style.RESET_ALL

commands = [create_dummy_user,create_user_options, set_password, set_privilege_level, update_points]

if __name__ == "__main__":
    while True:
        main()