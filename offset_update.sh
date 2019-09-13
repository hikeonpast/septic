#! /bin/bash
#takes a float on the command line and updates the config database accordingly
#not safe for use by folks with bad intentions or fat fingers

offset=$1
if [[ $offset =~ ^[+-]?[0-9]+\.?[0-9]*$ ]];then
	echo "Updating offset to" $offset "inches"
	command=$(printf "psql test -c \"update config set value='%s' where key='hose_offset';\"" $offset)

	eval $command

else
echo "was not a floating point; no change made"
fi
