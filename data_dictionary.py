#!/usr/bin/python3
# -*- coding: utf-8 -*-
import json
import sys
from ertelecom.checklist import md5, save_checklist
from ertelecom.metaposter import MetaPoster
from ertelecom.metacollectorch import MetaCollectorCH
from ertelecom.metacollectorhive import MetaCollectorHive

DEBUG = False

SPACE_KEY = "BD"
WORKLIST_FILE = "worklist.json"
CONNECTIONS_FILE = "connections.json"
CHECKLIST_FILE = "checklist.json"


if __name__ == "__main__":
    if (len(sys.argv) == 2 and sys.argv[1] == "DEBUG") or DEBUG is True:
        print("[!] Running in DEBUG mode, page names cnanged Table->Nable_dbg, Database->Natabase_dbg and Hive->Nive")
        DEBUG = True

    done_list = {} # to save checksums and page_ids of processed pages

    with open(WORKLIST_FILE, "r") as worklist_file, open(CONNECTIONS_FILE, "r") as connections_file:
        worklist = json.load(worklist_file)
        connections = json.load(connections_file)

        # ClickHouse
        print("[Posting ClickHouse db list page]")
        databases_list_page_id = MetaPoster.make_root_page(
            SPACE_KEY,
            connections["clickhouse"]["kb_page"] if not DEBUG else connections["clickhouse"]["kb_page_debug"],
            "ClickHouse Data Dictionary" if not DEBUG else "Nive Data Dictionary - CH",
            worklist,
            "clickhouse",
            (connections["confluence"]["user"], connections["confluence"]["password"]),
        )
        for wl_db in worklist["clickhouse"]:
            if wl_db["page_status"] in ("add", "update"):
                mc = MetaCollectorCH(wl_db, connections)
                mc.execute()
                mp = MetaPoster(SPACE_KEY, wl_db, connections, "clickhouse", DEBUG)
                mp.execute(databases_list_page_id)
            comments_file_name = connections["clickhouse"]["comments_path"]+wl_db["name"]+".json"
            done_list[comments_file_name] = {}
            done_list[comments_file_name]["md5"] = md5(comments_file_name)

        # Hive
        print("[Posting Hive db list page]")
        databases_list_page_id = MetaPoster.make_root_page(
            SPACE_KEY,
            connections["hive"]["kb_page"] if not DEBUG else connections["hive"]["kb_page_debug"],
            "Hive Data Dictionary" if not DEBUG else "Nive Data Dictionary - HV",
            worklist,
            "hive",
            (connections["confluence"]["user"], connections["confluence"]["password"]),
        )
        for wl_db in worklist["hive"]:
            if wl_db["page_status"] in ("add", "update"):
                mc = MetaCollectorHive(wl_db, connections)
                mc.execute()
                mp = MetaPoster(SPACE_KEY, wl_db, connections, "hive", DEBUG)
                mp.execute(databases_list_page_id)
            comments_file_name = connections["hive"]["comments_path"]+wl_db["name"]+".json"
            done_list[comments_file_name] = {}
            done_list[comments_file_name]["md5"] = md5(comments_file_name)

    # Save all page_ids and meta checksums to be compared at next run
    save_checklist(done_list, CHECKLIST_FILE)
