
import logging
import telnetlib


class TelnetWrapper:
    """ Telnet based wrapper for CMaNGOS interaction
    """
    # TODO DOC
    def __init__(self, host: str, port: str, user: str, pwd: str, log_level=logging.INFO):
        logging.basicConfig(filename='../../wrapper.log', level=log_level)
        self.host = host
        self.port = port
        self.user = user
        self.pwd = pwd
        logging.debug('Opening a Telnet session on', self.host, ':', self.port)
        self.tn_client = telnetlib.Telnet(host=host, port=port)
        logging.info('Telnet client connected to ', self.tn_client.host, ':', self.tn_client.port)
        self.connect()

    def connect(self):
        # TODO DOC
        logging.debug('Waiting for username prompt')
        self.tn_client.read_until(b"Username:")
        logging.debug('Sending username', self.user)
        self.tn_client.write(self.user.encode('ascii') + b" \n")
        logging.debug('Waiting for password prompt')
        self.tn_client.read_until(b"Password:")
        logging.debug('Sending password', self.pwd)
        self.tn_client.write(self.pwd.encode('ascii') + b" \n")
        self.wait_cli_prompt()
        logging.info('Successfully connected as', self.user)

    def wait_cli_prompt(self):
        # TODO DOC
        logging.debug('Waiting for a ready cli prompt')
        self.tn_client.read_until(b"mangos>", timeout=1)
        logging.debug('Sending a newline character')
        self.tn_client.write(b"\n")
        logging.debug('Waiting for a ready cli prompt')
        self.tn_client.read_until(b"mangos>")
        logging.debug('Cli prompt ready')

    def close(self):
        # TODO DOC
        logging.debug('Disconnecting', self.user, '; exiting cli prompt')
        self.tn_client.write(b"quit \n")
        logging.info('Closing Telnet connection to', self.host, ':', self.port)
        self.tn_client.close()

    def get_online_accounts(self):
        # TODO DOC
        self.wait_cli_prompt()
        accounts = {}
        logging.debug('Requesting online account list')
        self.tn_client.write(b"account onlinelist \n")
        result = str(self.tn_client.read_until(b"mangos>"))
        logging.debug('Response', result)
        result = result.replace('\\r', '').split('\\n')[3:-2]
        for account in result:
            (id, username, character, ip, gm, expansion) = account[1:-1].split("|")
            accounts[id.strip()] = {
                'id': id.strip(),
                'username': username.strip(),
                'character': character.strip(),
                'ip': ip.strip(),
                'gm': gm.strip(),
                'expansion': expansion.strip()
            }
        return accounts

    def shutdown_server(self, delay: int = 1):
        # TODO DOC
        self.wait_cli_prompt()
        logging.debug('Requesting server shutdown in', delay, 'second(s)')
        self.tn_client.write(b"server shutdown " + str(delay).encode('ascii') + b" \n")
        self.close()
