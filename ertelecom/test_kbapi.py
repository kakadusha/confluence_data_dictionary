#!/usr/bin/python3
# -*- coding: utf-8 -*-
import json
import time
import requests
import sys
from kbapi import add_page, post_page, update_page, get_version, add_or_update_page, delete_page


DATA = {"space": {"key": "BD"}}
CONNECTIONS_FILE = "connections.json"
SPACE_KEY = "BD"
KB_PARENT_PAGE = 345258453

if __name__ == "__main__":
    if len(sys.argv) == 2 and sys.argv[1] == "DEBUG":
        print("[!] Running in DEBUG mode, page names cnanged Table->Nable_dbg, Database->Natabase_dbg and Hive->Nive")
        DEBUG = True

    connections = {}
    try:
        with open(CONNECTIONS_FILE, "r") as connections_file:
            connections = json.load(connections_file)
    except FileNotFoundError as identifier:
        with open("../"+CONNECTIONS_FILE, "r") as connections_file:
            connections = json.load(connections_file)
    

    auth = (connections["confluence"]["user"], connections["confluence"]["password"])

    ### create and update ###
    title1 = f"test_kbapi created page on {str(time.time())}"
    page_id = add_page(
        SPACE_KEY, KB_PARENT_PAGE, title1, f"content: kbapi created page, version: {1}", auth
    )
    print(f" Created page {page_id}")
    page2id = update_page(
        SPACE_KEY, KB_PARENT_PAGE, page_id, title1, f"content: kbapi created page, version: {2}", auth
    )
    print(f" Updated page {page_id}, returned {page2id}")

    ### add or update 2 times
    title3 = f"test_kbapi create or update page on {str(time.time())}"
    page3id = add_or_update_page(SPACE_KEY, KB_PARENT_PAGE, title3, f"content: kbapi add or update page, version: {1}", auth)
    print(f" Created or updated page {page3id}")
    page4id = add_or_update_page(SPACE_KEY, KB_PARENT_PAGE, title3, f"content: kbapi add or update page, version: {2}", auth)
    print(f" Created or updated page {page4id}")

    keyb = input("Type D to delete created pages: ")

    if keyb == 'D' or keyb == 'd':
        delete_page(SPACE_KEY, page2id, auth)
        delete_page(SPACE_KEY, page3id, auth)