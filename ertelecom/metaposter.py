#!/usr/bin/python3
# -*- coding: utf-8 -*-

import json
from ertelecom.kbapi import post_page, update_page, get_version, add_or_update_page

META_FILENAME_PATTERN = "meta_{0}_{1}.json"  # e.g. meta_hive_dbname.json


class MetaPoster:
    def __init__(self, space_key, wl_db, connections, prefix, debug_flag):
        self.space_key = space_key
        self.wl_db = wl_db
        self.connections = connections
        self.prefix = prefix
        self.debug_flag = debug_flag

    DATATYPES_COLOR_DICT = {
        "tinyint": "44AACC",
        "smallint": "44AACC",
        "int": "44AACC",
        "int32": "44AACC",
        "int16": "44AACC",
        "int8": "44AACC",
        "integer": "44AACC",
        "bigint": "44AACC",
        "float": "44AACC",
        "double": "44AACC",
        "decimal": "44AACC",
        "numeric": "44AACC",
        "timestamp": "99CC22",
        "datetime": "99CC22",
        "date": "99CC22",
        "interval": "99CC22",
        "string": "FF8822",
        "varchar": "FF8822",
        "char": "FF8822",
    }

    @staticmethod
    def generate_databases_list_page(meta, prefix):
        rows = []
        rows.append("||База||Описание||")
        for database in meta[prefix]:
            rows.append(
                "|[{database}|{prefix}-database {database}]|{description}|".format(
                    database=database["name"],
                    prefix=prefix,
                    description=database.get("description") or "n/a",
                )
            )
        return "\n".join(rows)

    def __generate_tables_page(self, database):
        rows = []
        rows.append("||Таблица||Описание||")
        for table in database["tables"]:
            rows.append(
                "|[{table}|{prefix}table {database}.{table}]|{description}|".format(
                    database=database["name"],
                    prefix=(self.prefix+"-") if self.prefix!="hive" else "",  # to keep working old hive page names ("table database.name")
                    table=table["name"],
                    description=table["description"] if table["description"] else " ",
                )
            )
        return "\n".join(rows)

    def __generate_columns_page(self, database, table):
        def colorize_data_type(type):
            if not type:
                return " "

            for d in self.DATATYPES_COLOR_DICT:
                if type.lower().find(d) > -1:
                    return "{color:#" + self.DATATYPES_COLOR_DICT[d] + "}" + type + "{color}"
            else:
                if "decimal" in type.lower():
                    return "{color:#" + self.DATATYPES_COLOR_DICT["decimal"] + "}" + type + "{color}"
                if "varchar" in type.lower():
                    return "{color:#" + self.DATATYPES_COLOR_DICT["varchar"] + "}" + type + "{color}"

            return type

        rows = []

        rows.append("h2. Описание")

        for field in table["info"]:
            rows.append("||{label}|||{value}|".format(label=field[0], value=field[1]))

        rows.append("h2. Поля")
        rows.append("||Поле||Тип||Описание||Пример Данных||")
        for field in table["fields"]:
            ss = "|{field}|{type}|{description}|{sample}|".format(
                field=field["name"],
                type=colorize_data_type(field["type"]),
                description=field["description"] if field["description"] else " ",
                sample="_{color:#666666}" + (field["sample"] if field["sample"] else " ") + "{color}_",
            )
            rows.append(ss)

        return "\n".join(rows)

    def __generate_partitions_page(self, database, table):
        def format_stat(stat):
            if stat[1] <= 0.1:
                return "{:.2f}".format(stat[0])

            return "{color:#FF6666}*" + "{:.2f}".format(stat[0]) + "*{color}"

        def get_stat(table, partition_index, field, stat_type):
            partitions = list(table["statistics"].keys())
            stat = table["statistics"][partitions[partition_index]][field["name"]][stat_type]
            prev_stat = table["statistics"][partitions[partition_index + 1]][field["name"]][stat_type]
            stat_delta = abs(stat - prev_stat)
            return (stat, stat_delta)

        rows = []
        rows.append("h2. Партиции")

        for partition in table["partitions"]:
            rows.append("|{0}|{1}|".format(partition["name"], partition.get("count")))

        partitions = list(table["statistics"].keys())
        if len(partitions) < 3:
            return "\n".join(rows)

        rows.append("h2. Статистика")
        rows.append("||Поле||{part_1}|| ||{part_2}|| ||{part_3}|| ||".format(part_1=partitions[0], part_2=partitions[1], part_3=partitions[2]))
        rows.append("||    ||NULLs||DISTINCTs||NULLs||DISTINCTs||NULLs||DISTINCTs||")
        for field in table["fields"]:
            rows.append(
                "|{field}|{part_1_nulls}|{part_1_distincts}|{part_2_nulls}|{part_2_distincts}|{part_3_nulls}|{part_3_distincts}|".format(
                    field=field["name"],
                    part_1_nulls=format_stat(get_stat(table, 0, field, 0)),
                    part_1_distincts=format_stat(get_stat(table, 0, field, 1)),
                    part_2_nulls=format_stat(get_stat(table, 1, field, 0)),
                    part_2_distincts=format_stat(get_stat(table, 1, field, 1)),
                    part_3_nulls=format_stat(get_stat(table, 2, field, 0)),
                    part_3_distincts=format_stat(get_stat(table, 2, field, 1)),
                )
            )

        return "\n".join(rows)

    @staticmethod
    def make_root_page(space_key, root_page_id, name, config, prefix, auth):
        content = MetaPoster.generate_databases_list_page(config, prefix)
        databases_list_page_id = add_or_update_page(space_key, root_page_id, name, content, auth, print_error_responce=False)
        return databases_list_page_id

    def post(self, meta, databases_list_page_id):
        if meta is None:
            return
        auth = (self.connections["confluence"]["user"], self.connections["confluence"]["password"])
        for database in meta:
            comments_file_name = self.connections[self.prefix]["comments_path"]+database['name']+".json"
            content = self.__generate_tables_page(database)
            print(f"# Posting database {self.prefix}/{database['name']}")
            database_page_id = add_or_update_page(
                self.space_key,
                databases_list_page_id,
                "{prefix}-{title} {db}".format(
                    prefix=self.prefix,
                    title="database" if not self.debug_flag else "natabase_dbg",
                    db=database["name"],
                ),
                content,
                auth
            )
            for table in database["tables"]:
                print(f"- posting table {database['name']}.{table['name']}")
                if not table.get("is_corrupted") and table.get("is_legal"):
                    content = self.__generate_columns_page(database, table)
                    columns_page_id = add_or_update_page(
                        self.space_key,
                        database_page_id,
                        "{prefix}{title} {db}.{table}".format(
                            prefix=(self.prefix+"-") if self.prefix != "hive" else "",  # to keep working old hive page names ("table database.name")
                            title="table" if not self.debug_flag else "nable_dbg",
                            db=database["name"],
                            table=table["name"],
                        ),
                        content,
                        auth,
                    )
                    if table["partitions"]:
                        content = self.__generate_partitions_page(database, table)
                        print(f"- - posting partitions {database['name']}.{table['name']}")
                        add_or_update_page(
                            self.space_key,
                            columns_page_id,
                            "{prefix}{title} {db}.{table} partitions".format(
                                prefix=(self.prefix+"-") if self.prefix != "hive" else "",  # to keep working old hive page names ("table database.name")
                                title="table" if not self.debug_flag else "nable_dbg",
                                db=database["name"],
                                table=table["name"],
                            ),
                            content,
                            auth,
                        )
        return

    def execute(self, databases_list_page_id):
        # fixme: consider to move meta load to MAIN
        meta_file_name = META_FILENAME_PATTERN.format(self.prefix, self.wl_db["name"])
        with open(meta_file_name, "r") as meta_file:
            meta = json.load(meta_file)
            self.post(meta, databases_list_page_id)


