
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

    def achievement_state(self, username: str, achievement_id: int):
        # TODO DOC
        result = self.execute_command('achievement ' + username + ' ' + str(achievement_id) + ' \n')
        print(result)  # TODO
        return result  # TODO

    def achievement_set_complete(self, username: str, achievement_id: int):
        # TODO DOC
        result = self.execute_command('achievement add ' + username + ' ' + str(achievement_id) + ' \n')
        print(result)  # TODO
        return result  # TODO

    def achievement_remove(self, username: str, achievement_id: int):
        # TODO DOC
        result = self.execute_command('achievement remove ' + username + ' ' + str(achievement_id) + ' \n')
        print(result)  # TODO
        return result  # TODO

    def achievement_criteria_set_complete_progress(self, username: str, criteria_id: int):
        # TODO DOC
        result = self.execute_command('achievement criteria add ' + username + ' ' + str(criteria_id) + ' \n')
        print(result)  # TODO
        return result  # TODO

    def achievement_criteria_add_progress(self, username: str, criteria_id: int, change: int):
        # TODO DOC
        result = self.execute_command('achievement criteria add ' + username +
                                      ' ' + str(criteria_id) + ' ' + str(change) + ' \n')
        print(result)  # TODO
        return result  # TODO

    def achievement_criteria_reset_progress(self, username: str, criteria_id: int):
        # TODO DOC
        result = self.execute_command('achievement criteria remove ' + username + ' ' + str(criteria_id) + ' \n')
        print(result)  # TODO
        return result  # TODO

    def achievement_criteria_reduce_progress(self, username: str, criteria_id: int, change: int):
        # TODO DOC
        result = self.execute_command('achievement criteria remove ' + username +
                                      ' ' + str(criteria_id) + ' ' + str(change) + ' \n')
        print(result)  # TODO
        return result  # TODO

# AHBot commands -------------------------------------------------------------------------------------------------------

    def ahbot_reload_conf(self):
        # TODO DOC
        result = self.execute_command('ahbot reload \n')
        print(result)  # TODO
        return result  # TODO

    def ahbot_status(self, detailled: bool = False):
        # TODO DOC
        command = 'ahbot status '
        if detailled:
            command += 'all '
        command += ' \n'
        result = self.execute_command(command)
        print(result)  # TODO
        return result  # TODO

    def ahbot_reset_auction(self, force_all_rebuild: bool = False):
        # TODO DOC
        command = 'ahbot rebuild '
        if force_all_rebuild:
            command += 'all '
        command += ' \n'
        result = self.execute_command(command)
        print(result)  # TODO
        return result  # TODO

    def ahbot_set_all_quota(self, grey_items: int, white_items: int, green_items: int,
                            blue_items: int, purple_items: int, orange_items: int, yellow_items: int):
        # TODO DOC
        result = self.execute_command('ahbot items amount ' + str(grey_items) + ' ' + str(white_items) +
                                      ' ' + str(green_items) + ' ' + str(blue_items) + ' ' + str(purple_items) +
                                      ' ' + str(orange_items) + ' ' + str(yellow_items) + ' \n')
        print(result)  # TODO
        return result  # TODO

    def ahbot_set_grey_quota(self, grey_items: int):
        # TODO DOC
        result = self.execute_command('ahbot items amount grey ' + str(grey_items) + ' \n')
        print(result)  # TODO
        return result  # TODO

    def ahbot_set_white_quota(self, white_items: int):
        # TODO DOC
        result = self.execute_command('ahbot items amount white ' + str(white_items) + ' \n')
        print(result)  # TODO
        return result  # TODO

    def ahbot_set_green_quota(self, green_items: int):
        # TODO DOC
        result = self.execute_command('ahbot items amount green ' + str(green_items) + ' \n')
        print(result)  # TODO
        return result  # TODO

    def ahbot_set_blue_quota(self, blue_items: int):
        # TODO DOC
        result = self.execute_command('ahbot items amount blue ' + str(blue_items) + ' \n')
        print(result)  # TODO
        return result  # TODO

    def ahbot_set_purple_quota(self, purple_items: int):
        # TODO DOC
        result = self.execute_command('ahbot items amount purple ' + str(purple_items) + ' \n')
        print(result)  # TODO
        return result  # TODO

    def ahbot_set_orange_quota(self, orange_items: int):
        # TODO DOC
        result = self.execute_command('ahbot items amount orange ' + str(orange_items) + ' \n')
        print(result)  # TODO
        return result  # TODO

    def ahbot_set_yellow_quota(self, yellow_items: int):
        # TODO DOC
        result = self.execute_command('ahbot items amount yellow ' + str(yellow_items) + ' \n')
        print(result)  # TODO
        return result  # TODO

    def ahbot_set_ratios(self, alliance_ratio: int, horde_ratio: int, neutral_ratio: int):
        # TODO DOC
        result = self.execute_command('ahbot items ratio ' + str(alliance_ratio) +
                                      ' ' + str(horde_ratio) + ' ' + str(neutral_ratio) + ' \n')
        print(result)  # TODO
        return result  # TODO

    def ahbot_set_alliance_ratio(self, alliance_ratio: int):
        # TODO DOC
        result = self.execute_command('ahbot items ratio alliance ' + str(alliance_ratio) + ' \n')
        print(result)  # TODO
        return result  # TODO

    def ahbot_set_horde_ratio(self, horde_ratio: int):
        # TODO DOC
        result = self.execute_command('ahbot items ratio horde ' + str(horde_ratio) + ' \n')
        print(result)  # TODO
        return result  # TODO

    def ahbot_set_neutral_ratio(self, neutral_ratio: int):
        # TODO DOC
        result = self.execute_command('ahbot items ratio neutral ' + str(neutral_ratio) + ' \n')
        print(result)  # TODO
        return result  # TODO

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

    def send_mail(self, character: str, subject: str = '', message: str = ''):
        # TODO DOC
        result = self.execute_command('send mail ' + character + ' "' + subject + '" "' + message + '" \n')
        return 'Mail sent to ' in result

    def send_mass_mail(self, mask: str, subject: str = '', message: str = ''):
        # TODO DOC
        result = self.execute_command('send mass mail ' + mask + ' "' + subject + '" "' + message + '" \n')
        return 'Mail sent to ' in result

    def send_money(self, character: str, money: int, subject: str = '', message: str = ''):
        # TODO DOC
        result = self.execute_command('send money ' + character +
                                      ' "' + subject + '" "' + message + '" ' + str(money) + ' \n')
        return 'Mail sent to ' in result

    def send_mass_money(self, mask: str, money: int, subject: str = '', message: str = ''):
        # TODO DOC
        result = self.execute_command('send mass money ' + mask +
                                      ' "' + subject + '" "' + message + '" ' + str(money) + ' \n')
        return 'Mail sent to ' in result

    def send_items(self, character: str, items: dict, subject: str = '', message: str = ''):
        # TODO DOC
        command = 'send items ' + character + ' "' + subject + '" "' + message + '"'
        for item in items:
            command += ' ' + str(item) + ':' + str(items[item])
        command += ' \n'
        result = self.execute_command(command)
        return 'Mail sent to ' in result

    def send_mass_items(self, mask: str, items: dict, subject: str = '', message: str = ''):
        # TODO DOC
        command = 'send mass items ' + mask + ' "' + subject + '" "' + message + '"'
        for item in items:
            command += ' ' + str(item) + ':' + str(items[item])
        command += ' \n'
        result = self.execute_command(command)
        return 'Mail sent to ' in result

    def send_announce(self, message: str):
        # TODO DOC
        self.execute_command('announce ' + message + ' \n')

    def send_notification(self, message: str):
        # TODO DOC
        self.execute_command('notify ' + message + ' \n')

    def send_message(self, character: str, message: str = ''):
        # TODO DOC
        self.execute_command('send message ' + character + ' "' + message + '" \n')

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
# print(tn.account_create('test', 'test'))
# print(tn.account_set_password('test', '123456'))
# print(tn.account_set_addon('test', 3))
# print(tn.account_set_gm_level('test', 1))
# print(tn.send_items('arrandale', {27979: 1}), 'plop', 'message text')
# print(tn.get_online_accounts())
# print(tn.account_get_characters('test'))
# print(tn.account_delete('test'))
# tn.announce_chat('announce test')
# tn.notify_online('notify test')
tn.close()
