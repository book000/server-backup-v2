#/bin/bash
usage_exit() {
    echo "Usage: $0 [-h host] [-r port] [-u user] [-i identity] [-p passphrase] [-w password] [-f from] [-o output]" 1>&2
    exit 1
}

while getopts h:r:u:i:p:f:o: OPT
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
        p)  PASSPHRASE=$OPTARG
            ;;
        f)  FROM=$OPTARG
            ;;
        o)  OUTPUT=$OPTARG
            ;;
        \?) usage_exit
            ;;
    esac
done
TODAY=$(date +%Y-%m-%d)

SSHCMD="rsync -arhvzsP --no-o --no-g --no-p --progress --delete --backup --exclude-from='${OUTPUT}/ignores' -e 'ssh -o StrictHostKeyChecking=no -p $PORT -i $IDENTITY' --rsync-path='sudo rsync' --backup-dir="${OUTPUT}/$TODAY" $USERNAME@$HOSTNAME:$FROM ${OUTPUT}/latest"
expect -c "
    log_file /var/log/expect.log
    exp_internal 1
    set timeout -1
    spawn sh -c \"$SSHCMD\"
    expect {
        \"Enter passphrase for key\" {
            send -- \"$PASSPHRASE\n\"
        }
    }
    expect {
        \"total size is\" {
            interact
            expect eof
            catch wait result
        }
    }
    "
echo rsync.sh end
