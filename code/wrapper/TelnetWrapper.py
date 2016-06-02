
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
        logging.debug('Opening a Telnet session on ' + self.host + ':' + self.port)
        self.tn_client = telnetlib.Telnet(host=host, port=port)
        logging.info('Telnet client connected to ' + self.tn_client.host + ':' + self.tn_client.port)
        self.connect()

    def connect(self):
        # TODO DOC
        logging.debug('Waiting for username prompt')
        self.tn_client.read_until(b"Username:")
        logging.debug('Sending username : ' + self.user)
        self.tn_client.write(self.user.encode('ascii') + b" \n")
        logging.debug('Waiting for password prompt')
        self.tn_client.read_until(b"Password:")
        logging.debug('Sending password : ' + self.pwd)
        self.tn_client.write(self.pwd.encode('ascii') + b" \n")
        self.wait_cli_prompt()
        logging.info('Successfully connected as ' + self.user)

    def wait_cli_prompt(self):
        # TODO DOC
        logging.debug('Waiting for a ready cli prompt')
        self.tn_client.read_until(b"mangos>", timeout=0.2)
        logging.debug('Sending a newline character')
        self.tn_client.write(b"\n")
        logging.debug('Waiting for a ready cli prompt')
        self.tn_client.read_until(b"mangos>")
        logging.debug('Cli prompt ready')

    def close(self):
        # TODO DOC
        logging.debug('Disconnecting ' + self.user + '; exiting cli prompt')
        self.tn_client.write(b"quit \n")
        logging.info('Closing Telnet connection to ' + self.host + ':' + self.port)
        self.tn_client.close()

    def execute_command(self, command: str):
        # TODO DOC
        self.wait_cli_prompt()
        logging.info('Execute command : ' + command)
        self.tn_client.write(bytes(command, 'UTF-8'))
        result = str(self.tn_client.read_until(b"mangos>"))
        logging.debug('Response ' + result)
        return result

# Account commands -----------------------------------------------------------------------------------------------------

    def get_online_accounts(self):
        # TODO DOC
        accounts = {}
        result = self.execute_command('account onlinelist \n')
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

    def account_get_characters(self, username: str):
        # TODO DOC
        characters = {}
        result = self.execute_command('account characters ' + username + ' \n')
        result = result.replace('\\r', '').split('\\n')[3:-2]
        for character in result:
            (guid, char_name, char_race, char_class, char_level) = character[1:-1].split("|")
            characters[guid.strip()] = {
                'guid': guid.strip(),
                'name': char_name.strip(),
                'race': char_race.strip(),
                'class': char_class.strip(),
                'level': char_level.strip()
            }
        return characters

    def account_create(self, username: str, password: str):
        # TODO DOC
        result = self.execute_command('account create ' + username + ' ' + password + ' \n')
        return 'Account with this name already exist' not in result

    def account_set_password(self, username: str, password: str):
        # TODO DOC
        result = self.execute_command('account set password ' + username + ' ' + password + ' ' + password + ' \n')
        return 'The password was changed' in result

    def account_set_addon(self, username: str, addon: int):
        # TODO DOC
        if addon < 0:
            return False  # wrong value
        result = self.execute_command('account set addon ' + username + ' ' + str(addon) + ' \n')
        return 'has been granted ' + str(addon) + ' expansion rights.' in result

    def account_set_gm_level(self, username: str, gm_level: int):
        # TODO DOC
        if gm_level < 0 or gm_level > 3:
            return False  # wrong value
        result = self.execute_command('account set gmlevel ' + username + ' ' + str(gm_level) + ' \n')
        return 'You change security level of account ' in result

    def account_delete(self, username: str):
        # TODO DOC
        result = self.execute_command('account delete ' + username + ' \n')
        return 'Account deleted:' in result

# Achievement commands -------------------------------------------------------------------------------------------------

# TODO

# Item commands --------------------------------------------------------------------------------------------------------

# TODO

# AHBot commands -------------------------------------------------------------------------------------------------------

# TODO

# Auction commands -----------------------------------------------------------------------------------------------------

# TODO

# Ban commands ---------------------------------------------------------------------------------------------------------

# TODO

# Character commands ---------------------------------------------------------------------------------------------------

# TODO

# Debug commands -------------------------------------------------------------------------------------------------------

# TODO

# Ticket commands ------------------------------------------------------------------------------------------------------

# TODO

# Event commands -------------------------------------------------------------------------------------------------------

# TODO

# Guild commands -------------------------------------------------------------------------------------------------------

# TODO

# Honor commands -------------------------------------------------------------------------------------------------------

# TODO

# Learn commands -------------------------------------------------------------------------------------------------------

# TODO

# List commands --------------------------------------------------------------------------------------------------------

# TODO

# Lookup commands ------------------------------------------------------------------------------------------------------

# TODO

# NPC commands ---------------------------------------------------------------------------------------------------------

# TODO

# Reload commands ------------------------------------------------------------------------------------------------------

# TODO

# Reset commands -------------------------------------------------------------------------------------------------------

# TODO

# Send commands --------------------------------------------------------------------------------------------------------

# TODO

# Server commands ------------------------------------------------------------------------------------------------------

# TODO

    def shutdown_server(self, delay: int = 1):
        # TODO DOC
        self.wait_cli_prompt()
        logging.debug('Requesting server shutdown in ' + str(delay) + ' second(s)')
        self.tn_client.write(b"server shutdown " + str(delay).encode('ascii') + b" \n")
        self.close()

# Various commands -----------------------------------------------------------------------------------------------------

# TODO


tn = TelnetWrapper(host='10.0.0.125', port='3443', user='administrator', pwd='administrator')
print(tn.account_create('test', 'test'))
print(tn.account_set_password('test', '123456'))
print(tn.account_set_addon('test', 3))
print(tn.account_set_gm_level('test', 1))
print(tn.get_online_accounts())
print(tn.account_get_characters('test'))
print(tn.account_delete('test'))
tn.close()
