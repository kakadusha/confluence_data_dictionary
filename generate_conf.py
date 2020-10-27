#!/usr/bin/python3
# -*- coding: utf-8 -*-

# - вынимает из конфы checklist.json - список страниц с чексуммами их json-описаний и page_ids для поста страниц
# - считает чексуммы текущщих описаний *.comments и в случае расхождений формируем статус (page_status) в worklist.json
#     - есть страница, чексумма не поменялась -- пропускаем "unchanged"
#     - есть страница, чексумма поменялась -- делаем "update"
#     - нет страницы -- делаем "add"
# - data_dictionary модуль различает UPDATE, ADD и UNCHANGED в случае UPDATE использует предоставленные page_id-ы
import json
import os
import re
from ertelecom.checklist import md5, load_checklist


CONNECTIONS_FILE = "connections.json"
WORKLIST_FILE = "worklist.json"
CHECKLIST_FILE = "checklist.json"


def load_comments_folder(folder):
    checklist = load_checklist(CHECKLIST_FILE)
    files = [f for f in os.listdir(folder) if re.match(r".*\.json", f)]
    meta_part = []
    for file_name in files:
        with open(folder + file_name, "r") as comment_file:
            print(f"Loading {folder}{file_name}...")
            items = json.load(comment_file)
            database = list(items.keys())[0]
            tables_dict = items[database]["tables"]

        md5_file = md5(folder + file_name)
        md5_old = (checklist.get(folder + file_name) or {}).get("md5") or "-1"
        database_page = (checklist.get(folder + file_name) or {}).get("database_page") or -1
        table_pages = (checklist.get(folder + file_name) or {}).get("table_pages") or {}
        if md5_old == "-1":
            operation = "add"
            print(f" - new database, ADD needed ({md5_old} vs {md5_file})")
            meta_part.append(
                {"name": database, "tables": list(tables_dict.keys()), "skip_partitions": True, "page_status": operation}
            )
        elif md5_file != md5_old:
            operation = "update"
            print(f" - differnt checksums, UPDATE needed ({md5_old} vs {md5_file})")
            meta_part.append(
                {
                    "name": database,
                    "tables": list(tables_dict.keys()),
                    "skip_partitions": True,
                    "page_status": operation,
                    "database_page": database_page,
                    "table_pages": table_pages,
                }
            )
        else:
            operation = "unchanged"
            print(f" - no difference found, SKIPPING ({md5_old} vs {md5_file})")
            meta_part.append(
                {"name": database, "tables": list(tables_dict.keys()), "skip_partitions": True, "page_status": operation}
            )

    return meta_part


if __name__ == "__main__":
    meta = {}
    with open(WORKLIST_FILE, "w") as wl_file, open(CONNECTIONS_FILE, "r") as connections_file:
        connections = json.load(connections_file)
        meta["hive"] = load_comments_folder(connections["hive"]["comments_path"])
        meta["clickhouse"] = load_comments_folder(connections["clickhouse"]["comments_path"])
        print(f"Writing {wl_file}")
        json.dump(meta, wl_file, indent=4)
    print("Done")

