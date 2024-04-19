import paramiko
import subprocess
import os
import io
import time
from scp import SCPClient
from neo4j_dump import wait_for_complete
from bento.common.s3 import S3Bucket
from bento.common.utils import get_logger, LOG_PREFIX, APP_NAME

def downlaod_s3(s3_bucket, s3_file_key, log, file_key):
    # Upload to s3 bucket
    #dest = f"s3://{s3_bucket}/{s3_folder}"
    bucket = S3Bucket(s3_bucket)
    try:
        bucket.download_file(s3_file_key, file_key)
        log.info(f'Downloading neo4j dump file {os.path.basename(s3_file_key)} succeeded!')
    except Exception as e:
        log.error(e)

def neo4j_restore(neo4j_ip, neo4j_user, neo4j_key, s3_bucket, s3_file_key):
    is_shell = True
    TMP = "/tmp/"
    if LOG_PREFIX not in os.environ:
        os.environ[LOG_PREFIX] = 'Neo4j_Restore'
    os.environ[APP_NAME] = 'Neo4j_Restore'
    log = get_logger('Neo4j Restore')
    file_key = os.path.join(TMP, os.path.basename(s3_file_key))
    log.info(f"Start downloading from {s3_file_key}")
    downlaod_s3(s3_bucket, s3_file_key, log, file_key)
    host = neo4j_ip
    command = f"neo4j-admin load --from={file_key} --database=neo4j --force"
    if host in ['localhost', '127.0.0.1']:
        try:
            subprocess.call(command, shell = is_shell)
        except Exception as e:
            log.error(e)
    else:
        #cmd_list = ["sudo su - commonsdocker","sudo -i", "systemctl stop neo4j", command, "systemctl start neo4j"]
        cmd_list = ["sudo systemctl stop neo4j", command, "sudo systemctl start neo4j"]
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        pkey = paramiko.RSAKey.from_private_key(io.StringIO(neo4j_key))
        log.info("Start connecting to remote neo4j server")
        client.connect(host, username=neo4j_user, pkey=pkey, timeout=30)
        log.info("Connect to the remote server successfully")
        channel = client.invoke_shell()
        log.info(f"Uploading file {file_key} to remote server")
        scp = SCPClient(client.get_transport())
        local_file_key = file_key
        scp.put(local_file_key, file_key)
        ''''''
        try:
            for cmd in cmd_list:
                channel.send(cmd + "\n")
                while not channel.recv_ready():
                    time.sleep(0.1)
                #set up timer because channel.recv() will stuck when there is no more output
                recv_timeout = 3
                output_buffer = wait_for_complete(log, channel, recv_timeout)
                log.info(output_buffer)
        except Exception as e:
            log.error(e)
        client.close()