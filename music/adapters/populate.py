import os
from typing import List

from music.domainmodel.user import User
from music.domainmodel.artist import Artist
from music.domainmodel.album import Album
from music.domainmodel.track import Track
from music.domainmodel.review import Review
from music.domainmodel.genre import Genre
from music.adapters.csvdatareader import CSVReader


def create_tables(connection):
    with connection:
        # obtain a cursor from the connection
        cursor = connection.cursor()

        # create tables in the Database
        cursor.execute('''CREATE TABLE IF NOT EXISTS artists(
                    ID INT PRIMARY KEY     NOT NULL,
                    NAME VARCHAR(100) );''')

        cursor.execute('''CREATE TABLE IF NOT EXISTS albums(
                              ID INT PRIMARY KEY     NOT NULL,
                              TITLE VARCHAR(50)    NOT NULL,
                              TYPE VARCHAR(50),
                              RELEASE_YEAR DATE,
                              URL VARCHAR(100));
                              ''')

        cursor.execute('''CREATE TABLE IF NOT EXISTS tracks(
                              ID INT PRIMARY KEY     NOT NULL,
                              TITLE VARCHAR(50)    NOT NULL,
                              DURATION INT,
                              URL VARCHAR(100),
                              ALBUM_ID INT,
                              ARTIST_ID INT,
                              FOREIGN KEY(ALBUM_ID) REFERENCES ALBUMS(ID),
                              FOREIGN KEY(ARTIST_ID) REFERENCES ARTISTS(ID));
                              ''')

        cursor.execute('''CREATE TABLE IF NOT EXISTS genres(
                    ID INT PRIMARY KEY     NOT NULL,
                    NAME VARCHAR(50)    NOT NULL);''')

        cursor.execute('''CREATE TABLE IF NOT EXISTS track_genre_assoc(
                    TRACK_ID INT NOT NULL,
                    GENRE_ID INT NOT NULL,
                    PRIMARY KEY (TRACK_ID, GENRE_ID),
                    FOREIGN KEY(TRACK_ID) REFERENCES TRACKS(ID),
                    FOREIGN KEY(GENRE_ID) REFERENCES GENRES(ID));
                    ''')

        cursor.execute('''CREATE TABLE IF NOT EXISTS users(
                            ID INT PRIMARY KEY     NOT NULL,
                            NAME VARCHAR(50)    NOT NULL,
                            PASSWORD VARCHAR(100)    NOT NULL);''')

        cursor.execute('''CREATE TABLE IF NOT EXISTS reviews(
                                      TRACK_ID INT NOT NULL,
                                      USER_ID INT NOT NULL,
                                      REVIEW TEXT,
                                      RATING INT,
                                      TIMESTAMP DATE,
                                      Constraint PK_Users_Reviews Primary Key (TRACK_ID, USER_ID, TIMESTAMP),
                                      FOREIGN KEY(TRACK_ID) REFERENCES TRACKS(ID),
                                      FOREIGN KEY(USER_ID) REFERENCES USERS(ID));
                                      ''')


def populate_tables(connection):
    dir_name = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    albums_filename = os.path.join(dir_name, "adapters", "data", "raw_albums_excerpt.csv")
    tracks_filename = os.path.join(dir_name, "adapters", "data", "raw_tracks_excerpt.csv")

    reader = CSVReader(albums_filename, tracks_filename)

    reader.read_csv_files()

    albums = reader.dataset_of_albums
    artists = reader.dataset_of_artists
    genres = reader.dataset_of_genres
    tracks = reader.dataset_of_tracks

    # Add artists to the DB
    populate_artist_table(connection, artists)

    # Add albums to the DB
    populate_album_table(connection, albums)

    # Add genres to the DB
    populate_genre_table(connection, genres)

    # Add tracks to the DB
    populate_tracks_table(connection, tracks)

    # Add track-genre associations to the DB
    populate_track_genre_assoc_table(connection, tracks)


def populate_artist_table(connection, artists: set[Artist]):
    with connection:
        # obtain a cursor from the connection
        cursor = connection.cursor()
        # Use the original artist IDs from the CSV file
        records = [(artist.artist_id, artist.full_name) for artist in artists]
        cursor.executemany('INSERT INTO ARTISTS VALUES(?,?) ON CONFLICT do nothing', records)
        connection.commit()


def populate_album_table(connection, albums: set[Album]):
    with connection:
        cursor = connection.cursor()
        # Use the original album IDs from the CSV file
        records = [(album.album_id, album.title, album.album_type, album.release_year, album.album_url) for album in
                   albums]
        cursor.executemany('INSERT INTO ALBUMS (ID, TITLE, TYPE, RELEASE_YEAR, URL) VALUES(?,?,?,?,?) ON CONFLICT do nothing', records)
        connection.commit()


def populate_genre_table(connection, genres: set[Genre]):
    with connection:
        cursor = connection.cursor()
        records = [(genre.genre_id, genre.name) for genre in genres]
        cursor.executemany('INSERT INTO GENRES VALUES(?,?) ON CONFLICT do nothing', records)
        connection.commit()


def populate_tracks_table(connection, tracks: list[Track]):
    with connection:
        cursor = connection.cursor()
        # Use the original track IDs from the CSV file
        records = [
            (
                track.track_id,
                track.title,
                track.track_duration,
                track.track_url,
                track.album.album_id if track.album is not None else None,
                track.artist.artist_id if track.artist is not None else None,
            )
            for track in tracks
        ]
        cursor.executemany('INSERT INTO TRACKS VALUES(?,?,?,?,?,?) ON CONFLICT do nothing', records)
        connection.commit()


def populate_track_genre_assoc_table(connection, tracks: list[Track]):
    with connection:
        cursor = connection.cursor()
        records = [
            (track.track_id, genre.genre_id)
            for track in tracks
            for genre in track.genres
        ]
        cursor.executemany('INSERT INTO TRACK_GENRE_ASSOC VALUES(?,?) ON CONFLICT do nothing', records)
        connection.commit()
