import sqlite3
from typing import List, Any

from music.domainmodel.user import User
from music.domainmodel.artist import Artist
from music.domainmodel.album import Album
from music.domainmodel.track import Track
from music.domainmodel.review import Review
from music.domainmodel.genre import Genre
from music.adapters.populate import populate_tables, create_tables

# Connect to the SQLite database
connection = sqlite3.connect('tracks.db')


def create_and_populate_db():
    with connection:
        cursor = connection.cursor()

        # Check if any tables exist in the database
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()

        if len(tables) > 0:
            # At least one table exists, so the database is not empty
            print("The database already exists.")
        else:
            # No tables exist, so the database is empty
            print("Creating and populating tables in the database")
            create_tables(connection)
            # populate the DB tables from the provided csv files
            populate_tables(connection)


def execute_query(query: str, parameter=None):
    with connection:
        # obtain a cursor from the connection
        cursor = connection.cursor()
        if parameter is None:
            cursor.execute(query)
        else:
            cursor.execute(query, parameter)


def execute_query_get_all(query: str, parameter=None) -> list[Any]:
    with connection:
        # obtain a cursor from the connection
        cursor = connection.cursor()
        if parameter is None:
            cursor.execute(query)
        else:
            cursor.execute(query, parameter)
        result = cursor.fetchall()
        return result


def execute_query_get_one(query: str, parameter=None) -> str:
    with connection:
        # obtain a cursor from the connection
        cursor = connection.cursor()
        if parameter is None:
            cursor.execute(query)
        else:
            cursor.execute(query, parameter)
        result = cursor.fetchone()
        if result is None:
            return None
        return result[0]


def row_to_track_object(row, cursor) -> Track:
    track = None
    try:
        # TRACK columns: ID, TITLE, DURATION, URL, ALBUM_ID, ARTIST_ID
        track_id, title, duration, url, album_id, artist_id = row[0:6]
        track = Track(track_id, title)
        if type(duration) is int:
            track.track_duration = duration
        track.track_url = url

        if album_id is not None:
            album_row = cursor.execute(
                'SELECT ID, TITLE, TYPE, RELEASE_YEAR, URL FROM ALBUMS WHERE ID = ?',
                (album_id,)
            ).fetchone()
            if album_row is not None:
                album_id, album_title, album_type, release_year, album_url = album_row
                album = Album(album_id, album_title)
                album.album_type = album_type
                if type(release_year) is int:
                    album.release_year = release_year
                album.album_url = album_url
                track.album = album

        if artist_id is not None:
            artist_row = cursor.execute(
                'SELECT ID, NAME FROM ARTISTS WHERE ID = ?',
                (artist_id,)
            ).fetchone()
            if artist_row is not None:
                artist_id, artist_name = artist_row
                track.artist = Artist(artist_id, artist_name)

        genre_rows = cursor.execute(
            '''SELECT G.ID, G.NAME
               FROM GENRES G
               INNER JOIN TRACK_GENRE_ASSOC TGA ON G.ID = TGA.GENRE_ID
               WHERE TGA.TRACK_ID = ?''',
            (track_id,)
        ).fetchall()
        for genre_id, genre_name in genre_rows:
            track.add_genre(Genre(genre_id, genre_name))
    except ValueError as e:
        print(f"Skipping row due to invalid data: {e}")
    except IndexError as e:
        print(f"Skipping row due to invalid index: {e}")
    return track


def get_tracks_from_query(query: str, search_string: str, not_found_label: str) -> List[Track]:
    if not search_string or not search_string.strip():
        return []

    search_string = search_string.strip()
    with connection:
        cursor = connection.cursor()
        rows = cursor.execute(query, (search_string,)).fetchall()
        if len(rows) == 0:
            print(f'{not_found_label} {search_string} was not found')
            return []

        searched_tracks = []
        for row in rows:
            track = row_to_track_object(row, cursor)
            if track is not None:
                searched_tracks.append(track)
        return searched_tracks


def search_tracks_by_title(name_string: str) -> List[Track]:
    """Search tracks by name (case-insensitive partial match)."""
    query = '''SELECT * FROM TRACKS
               WHERE TITLE LIKE '%'||?||'%' '''
    return get_tracks_from_query(query, name_string, 'Title')


def search_tracks_by_album(name_string: str) -> List[Track]:
    """Search tracks by album title (case-insensitive partial match)."""
    query = '''
        SELECT TRACKS.*
        FROM TRACKS
        INNER JOIN ALBUMS ON TRACKS.ALBUM_ID = ALBUMS.ID
        WHERE ALBUMS.TITLE LIKE '%' || ? || '%'
    '''
    return get_tracks_from_query(query, name_string, 'Album')


def search_tracks_by_artist(name_string: str) -> List[Track]:
    """Search tracks by artist name (case-insensitive partial match)."""
    query = '''
        SELECT TRACKS.*
        FROM TRACKS
        INNER JOIN ARTISTS ON TRACKS.ARTIST_ID = ARTISTS.ID
        WHERE ARTISTS.NAME LIKE '%' || ? || '%'
    '''
    return get_tracks_from_query(query, name_string, 'Artist')


def search_tracks_by_genre(name_string: str) -> List[Track]:
    """Search tracks by genre name (case-insensitive partial match)."""
    query = '''
        SELECT TRACKS.*
        FROM TRACKS
        INNER JOIN TRACK_GENRE_ASSOC
            ON TRACKS.ID = TRACK_GENRE_ASSOC.TRACK_ID
        INNER JOIN GENRES
            ON TRACK_GENRE_ASSOC.GENRE_ID = GENRES.ID
        WHERE GENRES.NAME LIKE '%' || ? || '%'
    '''
    return get_tracks_from_query(query, name_string, 'Genre')


def get_users_with_reviews() -> List:
    """Get all users with their review information."""
    query = '''
        SELECT USERS.ID, USERS.NAME,
               REVIEWS.TRACK_ID, REVIEWS.REVIEW,
               REVIEWS.RATING, REVIEWS.TIMESTAMP
        FROM USERS
        LEFT JOIN REVIEWS ON USERS.ID = REVIEWS.USER_ID
    '''
    return execute_query_get_all(query)


def get_reviews_with_track_and_user() -> List:
    """Get all reviews with track and user information."""
    query = '''
        SELECT REVIEWS.REVIEW,
               REVIEWS.RATING,
               REVIEWS.TIMESTAMP,
               TRACKS.ID,
               TRACKS.TITLE,
               USERS.ID,
               USERS.NAME
        FROM REVIEWS
        INNER JOIN TRACKS ON REVIEWS.TRACK_ID = TRACKS.ID
        INNER JOIN USERS ON REVIEWS.USER_ID = USERS.ID
    '''
    return execute_query_get_all(query)


def get_track_count_by_artist() -> List:
    query = '''
        SELECT ARTISTS.NAME, COUNT(TRACKS.ID)
        FROM ARTISTS
        LEFT JOIN TRACKS ON ARTISTS.ID = TRACKS.ARTIST_ID
        GROUP BY ARTISTS.ID, ARTISTS.NAME
    '''
    return execute_query_get_all(query)


def get_track_count_by_genre() -> List:
    query = '''
        SELECT GENRES.NAME, COUNT(TRACK_GENRE_ASSOC.TRACK_ID)
        FROM GENRES
        LEFT JOIN TRACK_GENRE_ASSOC
            ON GENRES.ID = TRACK_GENRE_ASSOC.GENRE_ID
        GROUP BY GENRES.ID, GENRES.NAME
    '''
    return execute_query_get_all(query)


def get_review_count_by_user() -> List:
    query = '''
        SELECT USERS.NAME, COUNT(REVIEWS.USER_ID)
        FROM USERS
        LEFT JOIN REVIEWS
            ON USERS.ID = REVIEWS.USER_ID
        GROUP BY USERS.ID, USERS.NAME
    '''
    return execute_query_get_all(query)


def get_average_rating_by_track() -> List:
    query = '''
        SELECT TRACKS.TITLE, AVG(REVIEWS.RATING)
        FROM TRACKS
        LEFT JOIN REVIEWS
            ON TRACKS.ID = REVIEWS.TRACK_ID
        GROUP BY TRACKS.ID, TRACKS.TITLE
    '''
    return execute_query_get_all(query)



def get_top_genres() -> List:
    query = '''
        SELECT GENRES.NAME, COUNT(TRACK_GENRE_ASSOC.TRACK_ID) AS TRACK_COUNT
        FROM GENRES
        INNER JOIN TRACK_GENRE_ASSOC
            ON GENRES.ID = TRACK_GENRE_ASSOC.GENRE_ID
        GROUP BY GENRES.ID, GENRES.NAME
        ORDER BY TRACK_COUNT DESC
        LIMIT 3
    '''
    return execute_query_get_all(query)



# Imported after execute_query helpers so user_reviews can reuse them
from music.user_reviews import prompt_and_insert_user, prompt_and_insert_reviews


def create_app():
    create_and_populate_db()
    run_queries()


def run_queries():
    # Example: Print the total number of tracks from the database
    query = '''SELECT COUNT(*) FROM TRACKS'''
    print(f"Total tracks: {execute_query_get_one(query)}")

    # Example: Print the details of the first 10 tracks in the db
    query = '''SELECT ID, TITLE, DURATION, URL, ALBUM_ID, ARTIST_ID
               FROM TRACKS
               LIMIT 10 OFFSET 0'''
    tracks = execute_query_get_all(query)
    print("Printing details of first 10 tracks:")
    print(*tracks, sep='\n')

    # Example: Input field to search and call function that retrieves tracks based on title
    name_string = input("Enter the search string for track titles: ")
    searched_tracks = search_tracks_by_title(name_string)
    print(f"Total tracks with '{name_string}' in title is {len(searched_tracks)}")
    print(*searched_tracks, sep='\n')

    #  TODO (Task 1) Show tracks based on album title by calling search_tracks_by_album(album_string)
    album_string = input("Enter the search string for album titles: ")
    searched_tracks = search_tracks_by_album(album_string)
    print(f"Total tracks with '{album_string}' in album title is {len(searched_tracks)}")
    print(*searched_tracks, sep='\n')


    #  TODO (Task 1) Show tracks based on artist name by calling search_tracks_by_artist(artist_string)
    artist_string = input("Enter the search string for artist name: ")
    searched_tracks = search_tracks_by_artist(artist_string)
    print(f"Total tracks with '{artist_string}' in artist name is {len(searched_tracks)}")
    print(*searched_tracks, sep='\n')


    #  TODO (Task 1) Show tracks based on genre by calling search_tracks_by_genre(genre_name)
    genre_name = input("Enter genre name: ")
    searched_tracks = search_tracks_by_genre(genre_name)
    print(f"Total tracks with '{genre_name}' in genre is {len(searched_tracks)}")
    print(*searched_tracks, sep='\n')


    """ TODO (Task 1) Collect user details and insert a row into the users table
        HINT: Complete and use the prompt_and_insert_user() function to collect user details and insert a row into the users table 
        HINT: Complete and use the prompt_and_insert_reviews(user_id) function to collect reviews and insert rows into the reviews table 
        don't forget to remove the pass statement"""
    user_id = prompt_and_insert_user()
    if user_id is not None:
        prompt_and_insert_reviews(user_id)

    #  TODO (Task 1) Show all users with their review information by calling get_users_with_reviews()
    users_with_reviews = get_users_with_reviews()
    print("\nAll users with review information:")
    print(*users_with_reviews, sep='\n')


    #  TODO (Task 1) Show all reviews with track and user information by calling get_reviews_with_track_and_user()
    reviews = get_reviews_with_track_and_user()
    print("\nAll reviews with track and user information:")
    print(*reviews, sep='\n')

    #  TODO (Task 2) Show the total number of tracks by each artist by calling get_track_count_by_artist()
    track_counts = get_track_count_by_artist()
    print("\nTotal number of tracks by each artist:")
    print(*track_counts, sep='\n')

    #  TODO (Task 2) Show the total number of tracks in each genre by calling get_track_count_by_genre()
    track_counts_by_genre = get_track_count_by_genre()
    print("\nTotal number of tracks in each genre:")
    print(*track_counts_by_genre, sep='\n')

    #  TODO (Task 2) Show the total number of reviews written by each user by calling get_review_count_by_user()
    review_counts = get_review_count_by_user()
    print("\nTotal number of reviews written by each user:")
    print(*review_counts, sep='\n')

    #  TODO (Task 2) Show average ratings for tracks by calling get_average_ratings()
    average_ratings = get_average_rating_by_track()
    print("\nAverage rating for each track:")
    print(*average_ratings, sep='\n')

    #  TODO (Task 2) Show the most common genres by calling get_most_common_genres()
    top_genres = get_top_genres()
    print("\nTop 3 most common genres:")
    print(*top_genres, sep='\n')

