class Query:
    def __init__(self, table):
        self.table = table

        self._select = ["*"]
        self._where = []
        self._limit = None
        self._order = None

    def select(self, *columns):
        self._select = list(columns)
        return self

    def where(self, column, operator, value):
        self._where.append(
            (column, operator, value)
        )
        return self

    def limit(self, amount):
        self._limit = amount
        return self

    def order_by(self, column, direction="ASC"):
        self._order = (column, direction)
        return self