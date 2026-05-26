class Compiler:
    def compile(self, query):
        sql = []

        sql.append(
            f"SELECT {', '.join(query._select)}"
        )

        sql.append(f"FROM {query.table}")

        params = []

        if query._where:
            conditions = []

            for column, operator, value in query._where:
                conditions.append(
                    f"{column} {operator} ?"
                )

                params.append(value)

            sql.append(
                "WHERE " + " AND ".join(conditions)
            )

        if query._order:
            column, direction = query._order

            sql.append(
                f"ORDER BY {column} {direction}"
            )

        if query._limit:
            sql.append(
                f"LIMIT {query._limit}"
            )

        return " ".join(sql), params