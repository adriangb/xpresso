#!/bin/sh
wrk http://localhost:8080$1 -d5s -t4 -c64
