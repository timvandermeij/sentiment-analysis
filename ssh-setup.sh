#!/bin/bash

if [[ "x$1" = "x" ]]; then
	if [ ! -f hosts ]; then
		echo "Usage: ./ssh-setup.sh [hostsfile]"
		echo "Note: the hosts file MUST be of a format readable for OpenMPI."
		echo "Normal /etc/hosts often contains more information that needed,"
		echo "such as hostname aliases and other unrelated hosts."
		return
	fi
else
	cp "$1" hosts
fi

# Make root node the first node
root=`hostname -s`
sed -i "1s;^;$root\n;" hosts

echo "Updating ~/.ssh/config for agent forwarding..."
if [ -f ~/.ssh/config ]; then
	cp ~/.ssh/config ~/.ssh/config.bak
fi

header='### Added by ssh-setup.sh'
echo "$header" >> ~/.ssh/config
sed -i "/^$header/q" ~/.ssh/config # Remove everything after the first header

cut -d' ' -f1 hosts | while read -r node; do
	if [[ "$node" == \#* ]]; then
		continue
	fi
	echo "Host $node" >> ~/.ssh/config
	echo -e "\tForwardAgent yes" >> ~/.ssh/config
done

echo "Done. Now checking if all nodes are connectible."
echo "If any node listed below should not be a part of the hosts file,"
echo "Then quit this script, remove its line from the file, and rerun"
echo "./ssh-setup.sh without parameters, OR use a different base hosts file"
echo "as first parameter. You might want to mv ~/.ssh/config.bak ~/.ssh/config"
echo "in case anything went wrong, although rerunning should clean itself up."
echo "Any nodes that you trust, but give a warning of being not yet recognized"
echo "must have this question answered with yes."

cut -d' ' -f1 hosts | while read -r node; do
	if [[ "$node" == \#* ]]; then
		continue
	fi
	echo "Checking node $node..."
	ssh $node "echo OK" < /dev/null # Stop SSH from eating all input
done

echo "Done!"
