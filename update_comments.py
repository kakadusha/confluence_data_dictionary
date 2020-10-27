#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
    Updates comments in Hive tables by ALTER TABLE, takes comments from given file
    TODO: Add ClickHouse support, only Hive is supported
"""

import json
from pyhive import hive
import sys

CONNECTIONS_FILE = "connections.json"


def update_comments(cursor, database, table, columns):
    cursor.execute("SELECT * FROM {database}.{table} LIMIT 1".format(database=database, table=table))
    fields_meta = {}
    for field in cursor.description:
        fields_meta[field[0].split(".")[1]] = field[1].split("_TYPE")[0]

    print(json.dumps(fields_meta, indent=2))
    for column in list(columns["fields"].keys()):
        sql_string = "ALTER TABLE {database}.{table} CHANGE {column} {column} {type} COMMENT '{comment}'".format(
            database=database, table=table, column=column, type=fields_meta[column], comment=columns["fields"][column]
        )
        print(sql_string + ";")
        try:
            cursor.execute(sql_string)
        except Exception as e:
            print(str(e))


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage update_comments <cmments_file>")
        exit(1)

    with open(CONNECTIONS_FILE, "r") as connections_file:
        connections = json.load(connections_file)

        # conn = hive.Connection(
        #     host="bigdata-name1.ertelecom.ru", port=10000, username="hdfs", auth="KERBEROS", kerberos_service_name="hive", database="default"
        # )
        conn = hive.Connection(host=connections["hive"]["host"], username=connections["hive"]["username"],)
        cursor = conn.cursor()

        with open(sys.argv[1], "r") as comments_file:
            comments_dict = json.load(comments_file)
            for database in list(comments_dict.keys()):
                for table in list(comments_dict[database]["tables"].keys()):
                    print(f"{database}.{table}")
                    update_comments(cursor, database, table, comments_dict[database]["tables"][table])
