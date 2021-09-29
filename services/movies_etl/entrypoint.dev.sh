#!/bin/sh

while true
do
	echo "ETL process started."
#  python main.py --no-input
#   if [ $? -ne 0    ] ; then
#      continue
#   else
#       break
#   fi
   echo "ETL process ended."
   echo "Sleeping for 5 seconds…"
   sleep 5s
   echo "Completed"
done

exec "$@"
