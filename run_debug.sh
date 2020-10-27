#!/usr/bin/env bash
#set -x
##### should be exported in Jenkins #####
#HIVE_LOGIN="mytestname"
#HIVE_PASSW="mytestpass"
#KB_LOGIN="mytestnamekb"
#KB_PASSW="mytestpasskb"
#####
# Apply variables to connections.json template
#sed -e "s/{HIVE_LOGIN}/$HIVE_LOGIN/; s/{HIVE_PASSW}/$HIVE_PASSW/; \
#        s/{KB_LOGIN}/$KB_LOGIN/; s/{KB_PASSW}/$KB_PASSW/;" \
#        ./connections.json > ./credentials.json
#
#
#export PATH=$PATH:/opt/cloudera/parcels/AIRFLOW/bin/
#kinit -t /home/airflow/prod/.kerberos/airflow.keytab airflow
# 
##python3 clean_kb.py DEBUG
#
python3 generate_conf.py DEBUG
#
python3 data_dictionary.py DEBUG