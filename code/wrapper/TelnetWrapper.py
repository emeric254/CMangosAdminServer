
import logging
import telnetlib


class TelnetWrapper:
    """
    Telnet based command wrapper for CMaNGOS

    This class interact with a CMaNGOS server by Telnet connection.
    Functions return a boolean statement or formatted data.
    """
    def __init__(self, host: str, port: str, user: str, pwd: str, log_level=logging.INFO):
        # TODO DOC
        logging.basicConfig(filename='../../wrapper.log', level=log_level)
        self.host = host
        self.port = port
        self.user = user
        self.pwd = pwd
        self.tn_client = None
        self.open_session()
        self.connect()

    def is_session_open(self):
        """
        Return Telnet session state

        True if session established, False otherwise
        """
        return self.tn_client is not None and self.tn_client.get_socket()

    def open_session(self):
        """
        Try to open a Telnet session with the CMaNGOS server

        Do nothing if already in a connected state
        """
        logging.info('Try to open a Telnet session on ' + self.host + ':' + self.port)
        if not self.is_session_open():
            self.tn_client = telnetlib.Telnet(host=self.host, port=self.port)
            logging.info('Telnet client connected to ' + self.tn_client.host + ':' + self.tn_client.port)
        else:
            logging.info('Already connected to a Telnet session')

    def connect(self):
        """
        Try to login into CMaNGOS server cli prompt

        Wait for credential questions and answer them with given ones.
        """
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
        """
        Flush data stream before doing a command

        Make sure there is no more data available to read
        """
        logging.debug('Waiting for a ready cli prompt')
        self.tn_client.read_until(b"mangos>", timeout=0.2)
        logging.debug('Sending a newline character')
        self.tn_client.write(b"\n")
        logging.debug('Waiting for a ready cli prompt')
        self.tn_client.read_until(b"mangos>")
        logging.debug('Cli prompt ready')

    def disconnect(self):
        """
        Disconnect from CMaNGOS cli prompt

        Send 'quit' command to disconnect from CMaNGOS cli prompt
        """
        logging.debug('Disconnecting ' + self.user + '; exiting cli prompt')
        self.tn_client.write(b"quit \n")

    def close_session(self):
        """
        Close the Telnet session
        """
        logging.info('Closing Telnet connection to ' + self.host + ':' + self.port)
        self.tn_client.close()

    def close(self):
        """
        Disconnect from CMaNGOS cli prompt and close Telnet session
        """
        self.disconnect()
        self.close_session()

    def execute_command(self, command: str):
        """
        Execute a command into CMaNGOS cli prompt and return the result

        Send command into CMaNGOS cli prompt and read answered data
        :arg command 'str' to execute
        """
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
            (account_id, username, character, ip, gm, expansion) = account[1:-1].split("|")
            accounts[account_id.strip()] = {
                'id': account_id.strip(),
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

    def account_search_from_email(self, user_email: str, limit: int = 100):
        # TODO DOC
        accounts = {}
        result = self.execute_command('lookup account email ' + user_email + ' ' + str(limit) + ' \n')
        result = result.replace('\\r', '').split('\\n')[3:-2]
        for account in result:
            (account_id, username, character, ip, gm, expansion) = account[1:-1].split("|")
            accounts[account_id.strip()] = {
                'id': account_id.strip(),
                'username': username.strip(),
                'character': character.strip(),
                'ip': ip.strip(),
                'gm': gm.strip(),
                'expansion': expansion.strip()
            }
        return accounts

    def account_search_from_name(self, username: str, limit: int = 100):
        # TODO DOC
        accounts = {}
        result = self.execute_command('lookup account name ' + username + ' ' + str(limit) + ' \n')
        result = result.replace('\\r', '').split('\\n')[3:-2]
        for account in result:
            (account_id, username, character, ip, gm, expansion) = account[1:-1].split("|")
            accounts[account_id.strip()] = {
                'id': account_id.strip(),
                'username': username.strip(),
                'character': character.strip(),
                'ip': ip.strip(),
                'gm': gm.strip(),
                'expansion': expansion.strip()
            }
        return accounts

    def account_search_from_ip(self, ip_addr: str, limit: int = 100):
        # TODO DOC
        accounts = {}
        result = self.execute_command('lookup account ip ' + ip_addr + ' ' + str(limit) + ' \n')
        result = result.replace('\\r', '').split('\\n')[3:-2]
        for account in result:
            (account_id, username, character, ip, gm, expansion) = account[1:-1].split("|")
            accounts[account_id.strip()] = {
                'id': account_id.strip(),
                'username': username.strip(),
                'character': character.strip(),
                'ip': ip.strip(),
                'gm': gm.strip(),
                'expansion': expansion.strip()
            }
        return accounts

# Achievement commands -------------------------------------------------------------------------------------------------

    def achievement_state(self, username: str, achievement_id: int):
        # TODO DOC
        result = self.execute_command('achievement ' + username + ' ' + str(achievement_id) + ' \n')
        print(result)  # TODO
        return result  # TODO

    def achievement_search(self, achievement_name: str):
        # TODO DOC
        result = self.execute_command('lookup achievement ' + achievement_name + ' \n')
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

    def auction_show_alliance(self):
        # TODO DOC
        result = self.execute_command('auction alliance \n')
        print(result)  # TODO
        return result  # TODO

    def auction_show_horde(self):
        # TODO DOC
        result = self.execute_command('auction horde \n')
        print(result)  # TODO
        return result  # TODO

    def auction_show_goblin(self):
        # TODO DOC
        result = self.execute_command('auction goblin \n')
        print(result)  # TODO
        return result  # TODO

    def auction_add_item_alliance(self, item_id: int, item_count: int = 1, min_bid: int = 1, buy_out: int = None,
                                  long_duration: bool = False, very_long_duration: bool = False):
        # TODO DOC
        command = 'auction item alliance ' + str(item_id) + ':' + str(item_count) + ' '
        if buy_out:
            command += str(min_bid) + ' ' + str(buy_out) + ' '
        if long_duration:
            if very_long_duration:
                command += 'very'
            command += 'long'
        else:
            command += 'short'
        command += ' \n'
        result = self.execute_command(command)
        print(result)  # TODO
        return result  # TODO

    def auction_add_item_horde(self, item_id: int, item_count: int = 1, min_bid: int = 1, buy_out: int = None,
                               long_duration: bool = False, very_long_duration: bool = False):
        # TODO DOC
        command = 'auction item horde ' + str(item_id) + ':' + str(item_count) + ' '
        if buy_out:
            command += str(min_bid) + ' ' + str(buy_out) + ' '
        if long_duration:
            if very_long_duration:
                command += 'very'
            command += 'long'
        else:
            command += 'short'
        command += ' \n'
        result = self.execute_command(command)
        print(result)  # TODO
        return result  # TODO

    def auction_add_item_goblin(self, item_id: int, item_count: int = 1, min_bid: int = 1, buy_out: int = None,
                                long_duration: bool = False, very_long_duration: bool = False):
        # TODO DOC
        command = 'auction item goblin ' + str(item_id) + ':' + str(item_count) + ' '
        if buy_out:
            command += str(min_bid) + ' ' + str(buy_out) + ' '
        if long_duration:
            if very_long_duration:
                command += 'very'
            command += 'long'
        else:
            command += 'short'
        command += ' \n'
        result = self.execute_command(command)
        print(result)  # TODO
        return result  # TODO

# Ban commands ---------------------------------------------------------------------------------------------------------

    def ban_account(self, username: str, reason: str, bantime: str = '-1'):
        # TODO DOC
        result = self.execute_command('ban account ' + username + ' ' + bantime + ' ' + reason + ' \n')
        print(result)  # TODO
        return result  # TODO

    def ban_character(self, character: str, reason: str, bantime: str = '-1'):
        # TODO DOC
        result = self.execute_command('ban character ' + character + ' ' + bantime + ' ' + reason + ' \n')
        print(result)  # TODO
        return result  # TODO

    def ban_ip(self, ip_addr: str, reason: str, bantime: str = '-1'):
        # TODO DOC
        result = self.execute_command('ban ip ' + ip_addr + ' ' + bantime + ' ' + reason + ' \n')
        print(result)  # TODO
        return result  # TODO

    def ban_info_account(self, username: str):
        # TODO DOC
        result = self.execute_command('baninfo account ' + username + ' \n')
        print(result)  # TODO
        return result  # TODO

    def ban_info_character(self, character: str):
        # TODO DOC
        result = self.execute_command('baninfo character ' + character + ' \n')
        print(result)  # TODO
        return result  # TODO

    def ban_info_ip(self, ip_addr: str):
        # TODO DOC
        result = self.execute_command('baninfo ip ' + ip_addr + ' \n')
        print(result)  # TODO
        return result  # TODO

    def ban_list_account(self):
        # TODO DOC
        result = self.execute_command('banlist account \n')
        print(result)  # TODO
        return result  # TODO

    def ban_list_character(self):
        # TODO DOC
        result = self.execute_command('banlist character \n')
        print(result)  # TODO
        return result  # TODO

    def ban_list_ip(self):
        # TODO DOC
        result = self.execute_command('banlist ip \n')
        print(result)  # TODO
        return result  # TODO

    def ban_list_search_account(self, username: str):
        # TODO DOC
        result = self.execute_command('banlist account ' + username + ' \n')
        print(result)  # TODO
        return result  # TODO

    def ban_list_search_character(self, character: str):
        # TODO DOC
        result = self.execute_command('banlist character ' + character + ' \n')
        print(result)  # TODO
        return result  # TODO

    def ban_list_search_ip(self, ip_addr: str):
        # TODO DOC
        result = self.execute_command('banlist ip ' + ip_addr + ' \n')
        print(result)  # TODO
        return result  # TODO

    def unban_account(self, username: str):
        # TODO DOC
        result = self.execute_command('unban account ' + username + ' \n')
        print(result)  # TODO
        return result  # TODO

    def unban_character(self, character: str):
        # TODO DOC
        result = self.execute_command('unban character ' + character + ' \n')
        print(result)  # TODO
        return result  # TODO

    def unban_ip(self, ip_addr: str):
        # TODO DOC
        result = self.execute_command('unban ip ' + ip_addr + ' \n')
        print(result)  # TODO
        return result  # TODO

# Character commands ---------------------------------------------------------------------------------------------------

    def character_get_infos(self, character: str):
        result = self.execute_command('pinfo ' + character + ' \n')
        print(result)  # TODO
        return result  # TODO

    def character_achievements(self, character: str):
        # TODO DOC
        result = self.execute_command('character achievements ' + character + ' \n')
        print(result)  # TODO
        return result  # TODO

    def character_customize_at_next_login(self, character: str):
        # TODO DOC
        result = self.execute_command('character customize ' + character + ' \n')
        print(result)  # TODO
        return result  # TODO

    def character_rename_at_next_login(self, character: str):
        # TODO DOC
        result = self.execute_command('character rename ' + character + ' \n')
        print(result)  # TODO
        return result  # TODO

    def character_delete(self, character: str):
        # TODO DOC
        result = self.execute_command('character erase ' + character + ' \n')
        print(result)  # TODO
        return result  # TODO

    def character_get_reputation(self, character: str):
        # TODO DOC
        result = self.execute_command('character reputation ' + character + ' \n')
        print(result)  # TODO
        return result  # TODO

    def character_get_titles(self, character: str):
        # TODO DOC
        result = self.execute_command('character titles ' + character + ' \n')
        print(result)  # TODO
        return result  # TODO

    def character_stop_combat(self, character: str):
        # TODO DOC
        result = self.execute_command('combatstop ' + character + ' \n')
        print(result)  # TODO
        return result  # TODO

    def character_set_level(self, character: str, level: int = 0):
        # TODO DOC
        result = self.execute_command('character level ' + character + ' ' + str(level) + ' \n')
        print(result)  # TODO
        return result  # TODO

    def character_levelup(self, character: str, level: int = 1):
        # TODO DOC
        result = self.execute_command('levelup ' + character + ' ' + str(level) + ' \n')
        print(result)  # TODO
        return result  # TODO

    def character_mute(self, character: str, duration: int = 1):
        # TODO DOC
        result = self.execute_command('mute ' + character + ' ' + str(duration) + ' \n')
        print(result)  # TODO
        return result  # TODO

    def character_unmute(self, character: str):
        # TODO DOC
        result = self.execute_command('unmute ' + character + ' \n')
        print(result)  # TODO
        return result  # TODO

    def character_recall(self, character: str):
        # TODO DOC
        result = self.execute_command('recall ' + character + ' \n')
        print(result)  # TODO
        return result  # TODO

    def character_restore_deleted(self, character: str, new_name: str = '', account: str = ''):
        # TODO DOC
        result = self.execute_command('character deleted restore ' + character +
                                      ' ' + new_name + ' ' + account + ' \n')
        print(result)  # TODO
        return result  # TODO

    def character_delete_deleted(self, character: str):
        # TODO DOC
        result = self.execute_command('character deleted delete ' + character + ' \n')
        print(result)  # TODO
        return result  # TODO

    def character_delete_deleted_old(self):
        # TODO DOC
        result = self.execute_command('character deleted old \n')
        print(result)  # TODO
        return result  # TODO

    def character_delete_deleted_older_than(self, days: int):
        # TODO DOC
        result = self.execute_command('character deleted old ' + str(days) + ' \n')
        print(result)  # TODO
        return result  # TODO

    def character_deleted_list(self):
        # TODO DOC
        result = self.execute_command('character deleted list \n')
        print(result)  # TODO
        return result  # TODO

    def character_search_deleted_list(self, character: str):
        # TODO DOC
        result = self.execute_command('character deleted list ' + character + ' \n')
        print(result)  # TODO
        return result  # TODO

    def character_search_from_name(self, character: str, limit: int = 100):
        # TODO DOC
        result = self.execute_command('lookup player account ' + character + ' ' + str(limit) + ' \n')
        print(result)  # TODO
        return result  # TODO

    def character_search_from_email(self, email: str, limit: int = 100):
        # TODO DOC
        result = self.execute_command('lookup player email ' + email + ' ' + str(limit) + ' \n')
        print(result)  # TODO
        return result  # TODO

    def character_search_from_ip(self, ip_addr: str, limit: int = 100):
        # TODO DOC
        result = self.execute_command('lookup player ip ' + ip_addr + ' ' + str(limit) + ' \n')
        print(result)  # TODO
        return result  # TODO

    def character_reset_achievements(self, character: str):
        # TODO DOC
        result = self.execute_command('reset achievements ' + character + ' \n')
        print(result)  # TODO
        return result  # TODO

    def character_reset_honor(self, character: str):
        # TODO DOC
        result = self.execute_command('reset honor ' + character + ' \n')
        print(result)  # TODO
        return result  # TODO

    def character_reset_level(self, character: str):
        # TODO DOC
        result = self.execute_command('reset level ' + character + ' \n')
        print(result)  # TODO
        return result  # TODO

    def character_reset_specs(self, character: str):
        # TODO DOC
        result = self.execute_command('reset specs ' + character + ' \n')
        print(result)  # TODO
        return result  # TODO

    def character_reset_spells(self, character: str):
        # TODO DOC
        result = self.execute_command('reset spells ' + character + ' \n')
        print(result)  # TODO
        return result  # TODO

    def character_reset_stats(self, character: str):
        # TODO DOC
        result = self.execute_command('reset stats ' + character + ' \n')
        print(result)  # TODO
        return result  # TODO

    def character_reset_talents(self, character: str):
        # TODO DOC
        result = self.execute_command('reset talents ' + character + ' \n')
        print(result)  # TODO
        return result  # TODO

    def character_all_reset_spells(self):
        # TODO DOC
        result = self.execute_command('reset all spells \n')
        print(result)  # TODO
        return result  # TODO

    def character_all_reset_talents(self):
        # TODO DOC
        result = self.execute_command('reset all talents \n')
        print(result)  # TODO
        return result  # TODO

# Debug commands -------------------------------------------------------------------------------------------------------

    def debug_toggle_arenas(self):
        # TODO DOC
        result = self.execute_command('debug arena \n')
        print(result)  # TODO
        return result  # TODO

    def debug_toggle_battlegrounds(self):
        # TODO DOC
        result = self.execute_command('debug bg \n')
        print(result)  # TODO
        return result  # TODO

    def debug_show_spell_coefs(self, spell_id: int):
        # TODO DOC
        result = self.execute_command('debug spellcoefs ' + str(spell_id) + ' \n')
        print(result)  # TODO
        return result  # TODO

    def debug_mod_spells(self, spell_mask_bit_index: int, spell_mod_op: int, value: int, pct: bool = False):
        # TODO DOC
        command = 'debug spellmods '
        if pct:
            command += 'pct '
        else:
            command += 'flat '
        command += str(spell_mask_bit_index) + ' ' + str(spell_mod_op) + ' ' + str(value) + ' \n'
        result = self.execute_command(command)
        print(result)  # TODO
        return result  # TODO

# Ticket commands ------------------------------------------------------------------------------------------------------

    def ticket_delete_all(self):
        # TODO DOC
        result = self.execute_command('delticket all \n')
        print(result)  # TODO
        return result  # TODO

    def ticket_delete(self, ticket_id: int):
        # TODO DOC
        result = self.execute_command('delticket ' + str(ticket_id) + ' \n')
        print(result)  # TODO
        return result  # TODO

    def ticket_delete_from_character(self, character: str):
        # TODO DOC
        result = self.execute_command('delticket ' + character + ' \n')
        print(result)  # TODO
        return result  # TODO

    def ticket_gm_show_new_directly(self, activated: bool = True):
        # TODO DOC
        command = 'ticket '
        if activated:
            command += 'on'
        else:
            command += 'off '
        command += ' \n'
        result = self.execute_command(command)
        print(result)  # TODO
        return result  # TODO

    def ticket_show(self, ticket_id: int):
        # TODO DOC
        result = self.execute_command('ticket ' + str(ticket_id) + ' \n')
        print(result)  # TODO
        return result  # TODO

    def ticket_show_from_character(self, character: str):
        # TODO DOC
        result = self.execute_command('ticket ' + character + ' \n')
        print(result)  # TODO
        return result  # TODO

    def ticket_respond(self, ticket_id: int, response: str):
        # TODO DOC
        result = self.execute_command('ticket respond ' + str(ticket_id) + ' ' + response + ' \n')
        print(result)  # TODO
        return result  # TODO

    def ticket_respond_from_character(self, character: str, response: str):
        # TODO DOC
        result = self.execute_command('ticket respond ' + character + ' ' + response + ' \n')
        print(result)  # TODO
        return result  # TODO

# Event commands -------------------------------------------------------------------------------------------------------

    def event_get_details(self, event_id: int):
        # TODO DOC
        result = self.execute_command('event ' + str(event_id) + ' \n')
        print(result)  # TODO
        return result  # TODO

    def event_list(self):
        # TODO DOC
        result = self.execute_command('event list \n')
        print(result)  # TODO
        return result  # TODO

    def event_start(self, event_id: int):
        # TODO DOC
        result = self.execute_command('event start ' + str(event_id) + ' \n')
        print(result)  # TODO
        return result  # TODO

    def event_stop(self, event_id: int):
        # TODO DOC
        result = self.execute_command('event stop ' + str(event_id) + ' \n')
        print(result)  # TODO
        return result  # TODO

    def event_search(self, event_name: str):
        # TODO DOC
        result = self.execute_command('lookup event ' + str(event_name) + ' \n')
        print(result)  # TODO
        return result  # TODO

# Guild commands -------------------------------------------------------------------------------------------------------

    def guild_create(self, guild_name: str, guild_leader: str = ''):
        # TODO DOC
        result = self.execute_command('guild create "' + guild_name + '" ' + guild_leader + ' \n')
        print(result)  # TODO
        return result  # TODO

    def guild_delete(self, guild_name: str):
        # TODO DOC
        result = self.execute_command('guild delete "' + guild_name + '" \n')
        print(result)  # TODO
        return result  # TODO

    def guild_invite(self, character: str, guild_name: str):
        # TODO DOC
        result = self.execute_command('guild invite ' + character + ' "' + guild_name + '" \n')
        print(result)  # TODO
        return result  # TODO

    def guild_character_set_rank(self, character: str, rank: int):
        # TODO DOC
        result = self.execute_command('guild rank ' + character + ' ' + str(rank) + ' \n')
        print(result)  # TODO
        return result  # TODO

    def guild_uninvite(self, character: str):
        # TODO DOC
        result = self.execute_command('guild uninvite ' + character + ' \n')
        print(result)  # TODO
        return result  # TODO

# Honor commands -------------------------------------------------------------------------------------------------------

    def honor_reset(self, character: str):
        # TODO DOC
        result = self.execute_command('reset honor ' + character + ' \n')
        print(result)  # TODO
        return result  # TODO

# Learn commands -------------------------------------------------------------------------------------------------------

    def learn_all_default(self, character: str):
        # TODO DOC
        result = self.execute_command('learn all_default ' + character + ' \n')
        print(result)  # TODO
        return result  # TODO

    def learn_all_for_gm(self):
        # TODO DOC
        result = self.execute_command('learn all_gm \n')
        print(result)  # TODO
        return result  # TODO

# Lookup commands ------------------------------------------------------------------------------------------------------

    def area_search(self, area_name: str):
        # TODO DOC
        result = self.execute_command('lookup area ' + area_name + ' \n')
        print(result)  # TODO
        return result  # TODO

    def creature_search(self, creature_name: str):
        # TODO DOC
        result = self.execute_command('lookup creature ' + creature_name + ' \n')
        print(result)  # TODO
        return result  # TODO

    def currency_search(self, currency_name: str):
        # TODO DOC
        result = self.execute_command('lookup currency ' + currency_name + ' \n')
        print(result)  # TODO
        return result  # TODO

    def faction_search(self, faction_name: str):
        # TODO DOC
        result = self.execute_command('lookup faction ' + faction_name + ' \n')
        print(result)  # TODO
        return result  # TODO

    def item_search(self, item_name: str):
        # TODO DOC
        result = self.execute_command('lookup item ' + item_name + ' \n')
        print(result)  # TODO
        return result  # TODO

    def itemset_search(self, item_name: str):
        # TODO DOC
        result = self.execute_command('lookup itemset ' + item_name + ' \n')
        print(result)  # TODO
        return result  # TODO

    def object_search(self, object_name: str):
        # TODO DOC
        result = self.execute_command('lookup object ' + object_name + ' \n')
        print(result)  # TODO
        return result  # TODO

    def pool_search(self, pool_desc: str):
        # TODO DOC
        result = self.execute_command('lookup pool ' + pool_desc + ' \n')
        print(result)  # TODO
        return result  # TODO

    def quest_search(self, quest_name: str):
        # TODO DOC
        result = self.execute_command('lookup quest ' + quest_name + ' \n')
        print(result)  # TODO
        return result  # TODO

    def skill_search(self, skill_name: str):
        # TODO DOC
        result = self.execute_command('lookup skill ' + skill_name + ' \n')
        print(result)  # TODO
        return result  # TODO

    def spell_search(self, spell_name: str):
        # TODO DOC
        result = self.execute_command('lookup spell ' + spell_name + ' \n')
        print(result)  # TODO
        return result  # TODO

    def taxinode_search(self, taxinode_name: str):
        # TODO DOC
        result = self.execute_command('lookup taxinode ' + taxinode_name + ' \n')
        print(result)  # TODO
        return result  # TODO

    def tele_search(self, tele_name: str):
        # TODO DOC
        result = self.execute_command('lookup tele ' + tele_name + ' \n')
        print(result)  # TODO
        return result  # TODO

    def title_search(self, title_name: str):
        # TODO DOC
        result = self.execute_command('lookup title ' + title_name + ' \n')
        print(result)  # TODO
        return result  # TODO

# NPC commands ---------------------------------------------------------------------------------------------------------

    def npc_show_ai_infos(self):
        # TODO DOC
        result = self.execute_command('npc aiinfo \n')
        print(result)  # TODO
        return result  # TODO

    def npc_delete(self, npc_id: int):
        # TODO DOC
        result = self.execute_command('npc delete ' + str(npc_id) + ' \n')
        print(result)  # TODO
        return result  # TODO

    def npc_set_move_type(self, npc_id: int, stay: bool = False, random: bool = False,  delete_waypoints: bool = False):
        # TODO DOC
        command = 'npc setmovetype ' + str(npc_id) + ' '
        if stay:
            command += 'stay '
        elif random:
            command += 'random '
        else:
            command += 'way '
        if not delete_waypoints:
            command += 'NODEL '
        command += ' \n'
        result = self.execute_command(command)
        print(result)  # TODO
        return result  # TODO

# Dump commands ------------------------------------------------------------------------------------------------------

    def pdump_load(self, filename: str, username: str, newname: str = '', new_account_id: str = ''):
        # TODO DOC
        result = self.execute_command('pdump load ' + filename + ' ' + username +
                                      ' ' + newname + ' ' + new_account_id + ' \n')
        print(result)  # TODO
        return result  # TODO

    def pdump_write(self, filename: str, username: str):
        # TODO DOC
        result = self.execute_command('pdump write ' + filename + ' ' + username + ' \n')
        print(result)  # TODO
        return result  # TODO

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

    def server_save_all(self):
        # TODO DOC
        result = self.execute_command('saveall \n')
        print(result)  # TODO
        return result  # TODO

    def server_idle_restart(self, delay: int = 1):
        # TODO DOC
        result = self.execute_command('server idlerestart ' + str(delay) + ' \n')
        print(result)  # TODO
        return result  # TODO

    def server_cancel_idle_restart(self):
        # TODO DOC
        result = self.execute_command('server idlerestart cancel \n')
        print(result)  # TODO
        return result  # TODO

    def server_idle_shutdown(self, delay: int = 1):
        # TODO DOC
        result = self.execute_command('server idleshutdown ' + str(delay) + ' \n')
        print(result)  # TODO
        return result  # TODO

    def server_cancel_idle_shutdown(self):
        # TODO DOC
        result = self.execute_command('server idleshutdown cancel \n')
        print(result)  # TODO
        return result  # TODO

    def server_get_infos(self):
        # TODO DOC
        result = self.execute_command('server info \n')
        print(result)  # TODO
        return result  # TODO

    def server_get_log_filter(self):
        # TODO DOC
        result = self.execute_command('server log filter \n')
        print(result)  # TODO
        return result  # TODO

    def server_set_log_filter(self, log_filter_name: str, activation: bool):
        # TODO DOC
        command = 'server log filter ' + log_filter_name + ' '
        if activation:
            command += 'on '
        else:
            command += 'off '
        command += ' \n'
        result = self.execute_command(command)
        print(result)  # TODO
        return result  # TODO

    def server_get_log_level(self):
        # TODO DOC
        result = self.execute_command('server log level \n')
        print(result)  # TODO
        return result  # TODO

    def server_set_log_level(self, log_level: int):
        # TODO DOC
        result = self.execute_command('server log level ' + str(log_level) + ' \n')
        print(result)  # TODO
        return result  # TODO

    def server_get_motd(self):
        # TODO DOC
        result = self.execute_command('server motd \n')
        print(result)  # TODO
        return result  # TODO

    def server_set_motd(self, message: str):
        # TODO DOC
        result = self.execute_command('server set motd ' + message + ' \n')
        print(result)  # TODO
        return result  # TODO

    def server_restart(self, delay: int):
        # TODO DOC
        result = self.execute_command('server restart ' + str(delay) + ' \n')
        print(result)  # TODO
        return result  # TODO

    def server_cancel_restart(self):
        # TODO DOC
        result = self.execute_command('server restart cancel \n')
        print(result)  # TODO
        return result  # TODO

    def server_exit(self):
        # TODO DOC
        result = self.execute_command('server exit \n')
        print(result)  # TODO
        return result  # TODO

    def server_shutdown(self, delay: int):
        # TODO DOC
        result = self.execute_command('server shutdown ' + str(delay) + ' \n')
        print(result)  # TODO
        return result  # TODO

    def server_cancel_shutdown(self):
        # TODO DOC
        result = self.execute_command('server shutdown cancel \n')
        print(result)  # TODO
        return result  # TODO

    def server_check_expired_corpses(self):
        # TODO DOC
        result = self.execute_command('server corpses \n')
        print(result)  # TODO
        return result  # TODO

    def server_reload_config(self):
        # TODO DOC
        result = self.execute_command('reload config \n')
        print(result)  # TODO
        return result  # TODO

    def server_reload_all(self):
        # TODO DOC
        result = self.execute_command('reload all \n')
        print(result)  # TODO
        return result  # TODO

    def server_reload_achievements(self):
        # TODO DOC
        result = self.execute_command('reload all_achievement \n')
        print(result)  # TODO
        return result  # TODO

    def server_reload_areas(self):
        # TODO DOC
        result = self.execute_command('reload all_area \n')
        print(result)  # TODO
        return result  # TODO

    def server_reload_eventais(self):
        # TODO DOC
        result = self.execute_command('reload all_eventai \n')
        print(result)  # TODO
        return result  # TODO

    def server_reload_items(self):
        # TODO DOC
        result = self.execute_command('reload all_item \n')
        print(result)  # TODO
        return result  # TODO

    def server_reload_locales(self):
        # TODO DOC
        result = self.execute_command('reload all_locales \n')
        print(result)  # TODO
        return result  # TODO

    def server_reload_loots(self):
        # TODO DOC
        result = self.execute_command('reload all_loot \n')
        print(result)  # TODO
        return result  # TODO

    def server_reload_npcs(self):
        # TODO DOC
        result = self.execute_command('reload all_npc \n')
        print(result)  # TODO
        return result  # TODO

    def server_reload_quests(self):
        # TODO DOC
        result = self.execute_command('reload all_quest \n')
        print(result)  # TODO
        return result  # TODO

    def server_reload_scripts(self):
        # TODO DOC
        result = self.execute_command('reload all_script \n')
        print(result)  # TODO
        return result  # TODO

    def server_reload_spells(self):
        # TODO DOC
        result = self.execute_command('reload all_spell \n')
        print(result)  # TODO
        return result  # TODO

    def server_show_player_limits(self):
        # TODO DOC
        result = self.execute_command('server plimit \n')
        print(result)  # TODO
        return result  # TODO

    def server_set_player_number_limit(self, number: int):
        # TODO DOC
        result = self.execute_command('server plimit ' + str(number) + ' \n')
        print(result)  # TODO
        return result  # TODO

    def server_set_player_restrict_limit(self):
        # TODO DOC
        result = self.execute_command('server plimit player \n')
        print(result)  # TODO
        return result  # TODO

    def server_set_moderator_restrict_limit(self):
        # TODO DOC
        result = self.execute_command('server plimit moderator \n')
        print(result)  # TODO
        return result  # TODO

    def server_set_gamemaster_restrict_limit(self):
        # TODO DOC
        result = self.execute_command('server plimit gamemaster \n')
        print(result)  # TODO
        return result  # TODO

    def server_set_administrator_restrict_limit(self):
        # TODO DOC
        result = self.execute_command('server plimit administrator \n')
        print(result)  # TODO
        return result  # TODO

    def server_reset_player_limits(self):
        # TODO DOC
        result = self.execute_command('server plimit reset \n')
        print(result)  # TODO
        return result  # TODO

    def server_load_scripts(self, script_library_name: str):
        # TODO DOC
        result = self.execute_command('loadscripts ' + script_library_name + ' \n')
        print(result)  # TODO
        return result  # TODO

# Gobject commands -----------------------------------------------------------------------------------------------------

# TODO

    def gobject_add(self, gobject_id: int, spawn_time: int):
        # TODO DOC
        result = self.execute_command('gobject add ' + str(gobject_id) + ' ' + str(spawn_time) + ' \n')
        print(result)  # TODO
        return result  # TODO

    def gobject_delete(self, gobject_id: int):
        # TODO DOC
        result = self.execute_command('gobject delete ' + str(gobject_id) + ' \n')
        print(result)  # TODO
        return result  # TODO

    def gobject_move(self, gobject_id: int, x_pos: int, y_pos: int, z_pos: int):
        # TODO DOC
        result = self.execute_command('gobject move ' + str(gobject_id) +
                                      ' ' + str(x_pos) + ' ' + str(y_pos) + ' ' + str(z_pos) + ' \n')
        print(result)  # TODO
        return result  # TODO

    def gobject_turn(self, gobject_id: int, z_angle: int):
        # TODO DOC
        result = self.execute_command('gobject turn ' + str(gobject_id) + ' ' + str(z_angle) + ' \n')
        print(result)  # TODO
        return result  # TODO

    def gobject_set_phase_mask(self, gobject_id: int, phasemask: int):
        # TODO DOC
        result = self.execute_command('gobject setphase ' + str(gobject_id) + ' ' + str(phasemask) + ' \n')
        print(result)  # TODO
        return result  # TODO

    def gobject_get_location(self, gobject_id: int):
        # TODO DOC
        result = self.execute_command('gobject target ' + str(gobject_id) + ' \n')
        print(result)  # TODO
        return result  # TODO

# GM commands ----------------------------------------------------------------------------------------------------------

# TODO

    def gm_set_visiblity(self, visibility: bool = True):
        # TODO DOC
        command = 'gm visible '
        if visibility:
            command += 'on '
        else:
            command += 'off '
        command += ' \n'
        result = self.execute_command(command)
        print(result)  # TODO
        return result  # TODO

    def gm_set_fly(self, fly: bool = True):
        # TODO DOC
        command = 'gm fly '
        if fly:
            command += 'on '
        else:
            command += 'off '
        command += ' \n'
        result = self.execute_command(command)
        print(result)  # TODO
        return result  # TODO

    def gm_get_gm_mode(self):
        result = self.execute_command('gm \n')
        print(result)  # TODO
        return result  # TODO

    def gm_set_gm_mode(self, gm_mode: bool = True):
        # TODO DOC
        command = 'gm '
        if gm_mode:
            command += 'on '
        else:
            command += 'off '
        command += ' \n'
        result = self.execute_command(command)
        print(result)  # TODO
        return result  # TODO

    def gm_get_gm_mode_chat(self):
        result = self.execute_command('gm chat \n')
        print(result)  # TODO
        return result  # TODO

    def gm_set_gm_mode_chat(self, gm_mode_chat: bool = True):
        # TODO DOC
        command = 'gm chat '
        if gm_mode_chat:
            command += 'on '
        else:
            command += 'off '
        command += ' \n'
        result = self.execute_command(command)
        print(result)  # TODO
        return result  # TODO

    def gm_all_list(self):
        # TODO DOC
        result = self.execute_command('gm list \n')
        print(result)  # TODO
        return result  # TODO

    def gm_ingame_list(self):
        # TODO DOC
        result = self.execute_command('gm ingame \n')
        print(result)  # TODO
        return result  # TODO

# Various commands -----------------------------------------------------------------------------------------------------

# TODO

    def list_all_talents(self):
        # TODO DOC
        result = self.execute_command('list talents \n')
        print(result)  # TODO
        return result  # TODO

    def list_objects(self, object_id: int, limit: int = 10):
        # TODO DOC
        result = self.execute_command('list object ' + str(object_id) + ' ' + str(limit) + ' \n')
        print(result)  # TODO
        return result  # TODO

    def list_items(self, item_id: int, limit: int = 10):
        # TODO DOC
        result = self.execute_command('list item ' + str(item_id) + ' ' + str(limit) + ' \n')
        print(result)  # TODO
        return result  # TODO

    def list_creatures(self, creature_id: int, limit: int = 10):
        # TODO DOC
        result = self.execute_command('list item ' + str(creature_id) + ' ' + str(limit) + ' \n')
        print(result)  # TODO
        return result  # TODO

    def pool_get_infos(self, pool_id: int):
        # TODO DOC
        result = self.execute_command('pool ' + str(pool_id) + ' \n')
        print(result)  # TODO
        return result  # TODO

    def pool_get_list_spawned(self, pool_id: int):
        # TODO DOC
        result = self.execute_command('pool spawns ' + str(pool_id) + ' \n')
        print(result)  # TODO
        return result  # TODO

    def title_set_mask(self, title_mask: str):
        # TODO DOC
        result = self.execute_command('titles setmask ' + title_mask + ' \n')
        print(result)  # TODO
        return result  # TODO

    def tele_delete(self, tele_name: str):
        # TODO DOC
        result = self.execute_command('tele del ' + tele_name + ' \n')
        print(result)  # TODO
        return result  # TODO

    def tele_character(self, tele_name: str, character: str):
        # TODO DOC
        result = self.execute_command('tele name ' + character + ' ' + tele_name + ' \n')
        print(result)  # TODO
        return result  # TODO

    def whispers_gm_accept(self, activation: bool = True):
        # TODO DOC
        command = 'whispers '
        if activation:
            command += 'on '
        else:
            command += 'off '
        command += ' \n'
        result = self.execute_command(command)
        print(result)  # TODO
        return result  # TODO

    def kick_character(self, character: str):
        # TODO DOC
        result = self.execute_command('kick ' + character + ' \n')
        print(result)  # TODO
        return result  # TODO

    def instance_get_infos(self):
        # TODO DOC
        result = self.execute_command('instance stats \n')
        print(result)  # TODO
        return result  # TODO

    def arena_point_flush(self):
        # TODO DOC
        result = self.execute_command('flusharenapoints \n')
        print(result)  # TODO
        return result  # TODO


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
