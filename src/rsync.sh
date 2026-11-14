#!/bin/bash
usage_exit() {
    echo "Usage: $0 [-h host] [-r port] [-u user] [-i identity] [-k host_key_checking] [-f from] [-o output]" 1>&2
    exit 1
}

HOST_KEY_CHECKING=accept-new
while getopts h:r:u:i:k:f:o: OPT
do
    case $OPT in
        h)  HOSTNAME=$OPTARG
            ;;
        r)  PORT=$OPTARG
            ;;
        u)  USERNAME=$OPTARG
            ;;
        i)  IDENTITY=$OPTARG
            ;;
        k)  HOST_KEY_CHECKING=$OPTARG
            ;;
        f)  FROM=$OPTARG
            ;;
        o)  OUTPUT=$OPTARG
            ;;
        \?) usage_exit
            ;;
    esac
done

case $HOST_KEY_CHECKING in
    accept-new|yes|no) ;;
    *) usage_exit ;;
esac

if [ -z "${SSH_PASSPHRASE+x}" ]; then
    echo "ERROR: SSH_PASSPHRASE is not set" 1>&2
    exit 1
fi

TODAY=$(date +%Y-%m-%d)

mkdir -p "${OUTPUT}/$TODAY"

chmod 600 "${IDENTITY}"

SSHCMD="rsync -arhvzsP --no-o --no-g --no-p --progress --delete --backup --exclude-from='${OUTPUT}/ignores' -e 'ssh -o StrictHostKeyChecking=$HOST_KEY_CHECKING -o UserKnownHostsFile=${OUTPUT}/known_hosts -p $PORT -i $IDENTITY' --rsync-path='sudo rsync' --backup-dir="${OUTPUT}/$TODAY" $USERNAME@$HOSTNAME:$FROM ${OUTPUT}/latest"
expect -c "
    set timeout -1
    spawn sh -c \"$SSHCMD\"
    expect {
        \"Enter passphrase for key\" {
            send -- \"\$env(SSH_PASSPHRASE)\n\"
            exp_continue
        }
        eof
    }
    catch wait result
    exit [lindex \$result 3]
    "
STATUS=$?
echo rsync.sh end
exit $STATUS
