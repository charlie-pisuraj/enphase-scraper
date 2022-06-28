#!/bin/bash

/usr/bin/docker run -d --network=host --name clickhouse-server --ulimit nofile=262144:262144 clickhouse/clickhouse-server
/usr/bin/docker run -d --name=grafana --network=host -e "GF_INSTALL_PLUGINS=vertamedia-clickhouse-datasource" grafana/grafana

./script/create_schedule.py
