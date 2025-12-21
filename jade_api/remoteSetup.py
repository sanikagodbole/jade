# import paramiko
#
#
# def sftp_connect(hostname, username, password, port=22):
#     hostname = 'myfile.scad.edu'
#     username = 'sgodbo20'
#     password = 'Euphoria%200'
#     port = 22
#
#     SSH_Client = paramiko.SSHClient()
#     SSH_Client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
#     SSH_Client.connect(hostname=hostname,
#                        port=port,
#                        username=username,
#                        password=password,
#                        look_for_keys=False)
#
#     sftp_client = SSH_Client.open_sftp()
#     print("Connection successfully established ... ")

# remoteSetup.py
import paramiko

def sftp_connect(hostname, username, password, port=22):
    """Establishes an SFTP connection using provided credentials."""
    try:
        SSH_Client = paramiko.SSHClient()
        SSH_Client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        SSH_Client.connect(
            hostname=hostname,
            port=port,
            username=username,
            password=password,
            look_for_keys=False
        )

        sftp_client = SSH_Client.open_sftp()
        print(f"Connection successfully established to {hostname}")
        return sftp_client, SSH_Client # Return clients so you can use them to upload
    except Exception as e:
        print(f"SFTP Connection Error: {e}")
        return None, None