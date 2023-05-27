#!/bin/bash
for envfile in $(find . -maxdepth 1 -type f -name '.env.*'); do
    for line in $(cat ${envfile}); do
        # exclude comments
        if [[ "${line:0:1}" == "#" ]]; then
            continue
        fi

        match_line=$(echo ${line} | grep -E "^[A-Za-z0-9_].+=.+$")
        if [[ ${match_line} == "" ]]; then
            echo "Error in file: ${envfile}: line: ${line}"
        fi
    done
done