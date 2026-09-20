class Favourite:
    def __init__(self, id: int, user, track, date=None):
        from datetime import datetime
        self.__id = id
        self.__user = user
        self.__track = track
        self.__date = date if date is not None else datetime.now()

    def __repr__(self):
        return f"<Favourite: User={self.user}, Track={self.__track}>"

    def __eq__(self, other):
        if not isinstance(other, Favourite):
            return False
        return self.id == other.id

    def __lt__(self, other):
        if not isinstance(other, Favourite):
            raise TypeError("Comparison must be between Favourite instances")
        return self.id < other.id

    def __hash__(self):
        return hash(self.id)

    @property
    def id(self):
        return self.__id

    @property
    def user(self):
        return self.__user

    @property
    def track(self):
        return self.__track

    @property
    def date(self):
        return self.__date
