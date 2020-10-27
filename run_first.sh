#!/usr/bin/env bash
# remove workfiles and saved MD5 values
rm worklist.json -f
rm checklist.json -f

##### should be exported in Jenkins #####
#HIVE_LOGIN="mytestname"
#HIVE_PASSW="mytestpass"
#KB_LOGIN="mytestnamekb"
#KB_PASSW="mytestpasskb"
#####
# Apply variables to connections.json template
sed -e "s/{HIVE_LOGIN}/$HIVE_LOGIN/; s/{HIVE_PASSW}/$HIVE_PASSW/; \
        s/{KB_LOGIN}/$KB_LOGIN/; s/{KB_PASSW}/$KB_PASSW/;" \
        ./connections_t.json > ./connections.json

python3 clean_kb.py