#!/usr/bin/python3
# -*- coding: utf-8 -*-

import json
import os
from datetime import datetime
from pyhive import hive

META_FILENAME_PATTERN = "meta_{0}_{1}.json"  # e.g. meta_hive_dbname.json


class MetaCollectorHive:
    def __init__(self, db_in_config, connections):
        self.db_in_config = db_in_config
        self.connections = connections
        with open(os.path.join(connections["hive"]["comments_path"], db_in_config["name"] + ".json"), "r") as comments_file:
            self.field_desc = json.load(comments_file)

    def get_tables_list_from_db(self, database):
        try:
            self.cursor.execute("SHOW TABLES IN {database}".format(database=database["name"]))
            result = self.cursor.fetchall()
        except Exception as e:
            print(f"[!] Exception on SHOW TABLES ... {database['name']}:")
            print(type(e))
            print(e.args)
            print(e)
            return []
        return [row[0] for row in result]

    def get_field_description(self, database, table, field, field_comment):
        if database.lower() not in self.field_desc:
            return "{color:#3e3e0e}" + field_comment + "{color}"

        if table.lower() not in self.field_desc[database.lower()]["tables"]:
            return "{color:#3e3e0e}" + field_comment + "{color}"

        if field.lower() not in self.field_desc[database.lower()]["tables"][table.lower()]["fields"]:
            return "{color:#3e3e0e}" + field_comment + "{color}"

        return self.field_desc[database.lower()]["tables"][table.lower()]["fields"][field.lower()]

    def get_table_description(self, database, table):
        if database.lower() not in self.field_desc:
            return None

        if table.lower() not in self.field_desc[database.lower()]["tables"]:
            return None

        return self.field_desc[database.lower()]["tables"][table.lower()]["comment"]

    def get_table_meta(self, database, table_name):
        def parse_description(database, table_name, description_data, sample_data):
            labels_dict = [
                ("comment", "Comment", False),
                ("Owner", "Owner", False),
                ("CreateTime", "Create Time", False),
                ("LastAccessTime", "Last Access Time", False),
                ("last_modified_time", "Last Modified Time", True),
                ("Location", "Location", False),
                ("Compressed", "Compressed", False),
                ("numPartitions", "Number Of Partitions", False),
                ("Table Type", "Table Type", False),
                ("InputFormat", "Format", False),
            ]

            def parse_info(row):
                def format_value(value, format):
                    if not format:
                        return value

                    return datetime.utcfromtimestamp(int(value)).strftime("%Y-%m-%d %H:%M:%S")

                for known_label in labels_dict:
                    if known_label[0] in row[0]:
                        return (known_label[1], format_value(row[1], known_label[2]))

                    if known_label[0] in row[1]:
                        return (known_label[1], format_value(row[2], known_label[2]))

                return None

            fields_list = []
            info_list = []
            description = None

            fields_list_fetch = True
            table_info_fetch = False

            for row in description_data[1:]:
                if fields_list_fetch:  # if we are parsing fields' section
                    if "# Detailed Table Information" in row[0]:  # if here start of Info section
                        fields_list_fetch = False
                        table_info_fetch = True
                    elif row[0] == "" and not row[1]:  # if empty line
                        pass
                    elif "# " in row[0]:  # if any other comment line
                        pass
                    elif row[0] and row[1]:
                        fields_list.append(
                            {
                                "name": row[0],
                                "type": row[1],
                                "description": self.get_field_description(database, table_name, row[0], row[2]),
                                "sample": ",".join(sample_data[row[0]]) if row[0] in sample_data else None,
                            }
                        )
                elif table_info_fetch:
                    if (row[0] and row[1]) or (row[1] and row[2]):
                        info_row = parse_info(row)
                        if info_row:
                            info_list.append(info_row)
                            if info_row[0] == "Comment":
                                description = info_row[1]

            return {
                "name": table_name,
                "is_legal": True,
                "description": self.get_table_description(database, table_name),
                "fields": fields_list,
                "info": info_list,
            }

        def parse_partitions_list(partitions_list):
            clean_list = []
            for partition in partitions_list:
                partition_name = partition[0]
                if "/" in partition_name:
                    clean_list.append(partition_name.split("/")[0])
                else:
                    clean_list.append(partition_name)
            clean_list = list(set(clean_list))
            clean_list.sort()
            return clean_list

        def get_partition_query(partition_name):
            return partition_name.split("=")[0] + "='" + partition_name.split("=")[1] + "'"

        def generate_partitions_statistics(database, table_name, partition_field):
            self.cursor.execute(
                "SELECT {field}, COUNT(*) as cnt FROM {database}.{table} GROUP BY {field}".format(
                    database=database, table=table_name, field=partition_field
                )
            )
            partitions_list = []
            for part in self.cursor.fetchall():
                partitions_list.append(
                    {"name": str(partition_field) + "=" + str(part[0]), "count": part[1],}
                )

            return partitions_list

        def generate_partitions_field_statistics(database, table_name, table_meta):
            partitions_stats = {}
            partitions = table_meta["partitions"][-4:]
            for partition in partitions:
                fields_stats = {}
                for field in table_meta["fields"]:
                    # disabled as too slow
                    # self.cursor.execute("SELECT COUNT({field}) FROM {database}.{table} WHERE {partition}".format(
                    #       database=database, table=table_name, field=field['name'], partition=get_partition_query(partition)))
                    # nulls = self.cursor.fetchone()[0]
                    # self.cursor.execute("SELECT COUNT(DISTINCT {field}) FROM {database}.{table} WHERE {partition}".format(
                    #   database=database, table=table_name, field=field['name'], partition=get_partition_query(partition)))
                    # distincts = self.cursor.fetchone()[0]
                    nulls = -1
                    distincts = -1

                    fields_stats[field["name"]] = (nulls, distincts)
                partitions_stats[partition["name"]] = fields_stats

            return partitions_stats

        try:
            self.cursor.execute("DESCRIBE FORMATTED {database}.{table}".format(database=database["name"], table=table_name))
            result = self.cursor.fetchall()
            description = result
            if not database.get("skip_partitions"):  # =do we have to describe partitions?
                try:
                    # describe partitions
                    result = self.cursor.execute("SHOW PARTITIONS {database}.{table}".format(database=database["name"], table=table_name))
                    result = self.cursor.fetchall()
                    partitions_list = result
                except Exception as e:
                    print("[!] Exception on SHOW PARTITIONS for {database}.{table}:".format(database=database["name"], table=table_name))
                    print(type(e))
                    print(e.args)
                    print(e)
                    partitions_list = []
            else:
                partitions_list = []

            # get sample
            try:
                result = self.cursor.execute("SELECT * FROM {database}.{table} LIMIT 5".format(database=database["name"], table=table_name))
                sample_data = self.cursor.fetchall()
                result = self.cursor.description
                field_names = [row[0].split(".")[1] for row in result]

                sample = {}
                for row in sample_data:
                    column = 0
                    for field_name in field_names:
                        if field_name not in sample:
                            sample[field_name] = []
                        if self.field_desc[database["name"].lower()]["tables"][table_name.lower()].get("sample_hide"):  # database.get("sample_hide")
                            sample[field_name].append("значение скрыто")
                        else:
                            sample[field_name].append(str(row[column]))
                        column = column + 1
            except Exception as e:
                print("[!] Exception while getting data sample for {database}.{table}:".format(database=database["name"], table=table_name))
                print(type(e))
                print(e.args)
                print(e)
                sample = {}

            table_meta = parse_description(database["name"], table_name, description, sample)
            partitions_list = parse_partitions_list(partitions_list)
            if not database.get("skip_partitions"):
                partition_field = partitions_list[0].split("=")[0]
                table_meta["partitions"] = generate_partitions_statistics(database["name"], table_name, partition_field)
                table_meta["statistics"] = generate_partitions_field_statistics(database["name"], table_name, table_meta)
            else:
                table_meta["partitions"] = []
                table_meta["statistics"] = []

            return table_meta
        except Exception as e:
            print("[!] Failed to DESCRIBE table {0}, check table DDL in : {1}.json".format(table_name, database["name"]))
            print(type(e))
            print(e.args)
            print(e)
            return {
                "name": table_name,
                "description": "*{color:red}Таблица некорректно описана, ошибка команды DESCRIBE, проверьте /COMMENTS{color}*",
                "is_corrupted": True,
                "fields": [],
                "info": [],
            }

    def get_table_statistics(self, database, table_name, table_meta):
        result = self.cursor.execute("SHOW PARTITIONS {database}.{table}".format(database=database["name"], table=table_name))
        result = self.cursor.fetchall()
        description = result

    def collect_meta(self):
        meta = []
        database = self.db_in_config
        table_name = "no_name"
        tables_list_actual = self.get_tables_list_from_db(database)
        tables_list_conf = database["tables"]
        tables_meta = []
        if len(tables_list_actual) == 0:
            print(f"[!] Failed to get table list from DB: {database['name']}")
            meta.append(
                {"name": database["name"] + " - not found in Hive", "description": "Please check worklist.json", "tables": [],}
            )
            return meta

        for table_name in tables_list_actual:
            if table_name in tables_list_conf:
                try:
                    one_meta = self.get_table_meta(database, table_name)
                except Exception as e:
                    print("[!] Table not found in DB, check worklist.json {0}")
                    print(type(e))
                    print(e.args)
                    print(e)
                    one_meta = {
                        "name": table_name,
                        "is_legal": False,
                        "description": "*{color:#AAAA44}Таблица не обнаружена в базе, проверьте описание в /COMMENTS{color}*",
                    }
            else:
                one_meta = {
                    "name": table_name,
                    "is_legal": False,
                    "description": "*{color:#AAAA44}Таблица не зарегистрирована в словаре /comments{color}*",
                }
            tables_meta.append(one_meta)

        meta.append(
            {"name": database["name"], "description": database.get("description"), "tables": tables_meta,}
        )
        return meta

    def execute(self):
        conn = hive.Connection(self.connections["hive"]["host"], username=self.connections["hive"]["username"],)

        self.cursor = conn.cursor()
        meta = self.collect_meta()
        with open(META_FILENAME_PATTERN.format("hive", self.db_in_config["name"]), "w") as meta_file:
            json.dump(meta, meta_file, indent=2)

