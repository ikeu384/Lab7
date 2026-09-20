from datetime import datetime

from music import execute_query, execute_query_get_all, execute_query_get_one


def get_next_user_id():
    max_id = execute_query_get_one('SELECT MAX(ID) FROM users')
    if max_id is None:
        return 1
    return max_id + 1


def insert_user(user_id, name, password):
    query = '''
        INSERT INTO users (ID, NAME, PASSWORD)
        VALUES (?, ?, ?)
    '''
    execute_query(query, (user_id, name, password))


def insert_review(track_id, user_id, review_text, rating, timestamp):
    query = '''
        INSERT INTO reviews (TRACK_ID, USER_ID, REVIEW, RATING, TIMESTAMP)
        VALUES (?, ?, ?, ?, ?)
    '''
    execute_query(
        query,
        (track_id, user_id, review_text, rating, timestamp)
    )


def prompt_and_insert_user():
    print("\n--- Create a user ---")
    name = input("Enter user name: ").strip()
    if name == '':
        print("User name cannot be empty.")
        return None

    password = input("Enter password (at least 7 characters): ").strip()
    if len(password) < 7:
        print("Password must be at least 7 characters.")
        return None

    user_id = get_next_user_id()
    insert_user(user_id, name.lower(), password)
    print(f"User '{name}' inserted with ID {user_id}.")
    return user_id


def prompt_and_insert_reviews(user_id):
    print("\n--- Add reviews ---")
    while True:
        more_reviews = input("Do you want to insert a review? (y/n): ").strip().lower()
        if more_reviews != 'y':
            print("Stopped inserting reviews.")
            break

        try:
            track_id = int(input("Enter the track ID to review: ").strip())
        except ValueError:
            print("Track ID must be an integer.")
            continue

        track_row = execute_query_get_all('SELECT ID FROM TRACKS WHERE ID = ?', (track_id,))
        if len(track_row) == 0:
            print(f"Track {track_id} was not found.")
            continue

        review_text = input("Enter review text: ").strip()
        try:
            rating = int(input("Enter rating (1-5): ").strip())
        except ValueError:
            print("Rating must be an integer.")
            continue

        if rating < 1 or rating > 5:
            print("Rating must be between 1 and 5.")
            continue

        timestamp = datetime.now().isoformat(timespec='seconds')
        insert_review(track_id, user_id, review_text, rating, timestamp)
        print(f"Review for track {track_id} inserted.")
