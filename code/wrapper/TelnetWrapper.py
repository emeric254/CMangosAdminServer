# -*- coding: utf-8 -*-

import logging
import telnetlib


class TelnetWrapper:
    """
    Telnet based command wrapper for CMaNGOS.

    This class interact with a CMaNGOS server by Telnet connection.
    Functions return a boolean statement or formatted data.
    """

    def __init__(self, host: str, port: str, user: str, pwd: str, log_level=logging.INFO):
        """
        Create an instance of this class.

        It'll open a Telnet session to a CMaNGOS server and log into it.
        :param host: CMaNGOS Telnet IP/hostname
        :param port: CMaNGOS Telnet port
        :param user: CMaNGOS admin account username
        :param pwd: CMaNGOS admin account password
        :param log_level: cf. logging.log_level
        """
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
        Return Telnet session state.

        True if session established, False otherwise
        :return: True if the session is opened with the CMaNGOS server
        """
        return self.tn_client is not None and self.tn_client.get_socket()

    def open_session(self):
        """
        Try to open a Telnet session with the CMaNGOS server.

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
        Try to login into CMaNGOS server cli prompt.

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
        Flush data stream before doing a command.

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
        Disconnect from CMaNGOS cli prompt.

        Send 'quit' command to disconnect from CMaNGOS cli prompt
        """
        logging.debug('Disconnecting ' + self.user + '; exiting cli prompt')
        self.tn_client.write(b"quit \n")

    def close_session(self):
        """
        Close the Telnet session.
        """
        logging.info('Closing Telnet connection to ' + self.host + ':' + self.port)
        self.tn_client.close()

    def close(self):
        """
        Disconnect from CMaNGOS cli prompt and close Telnet session.
        """
        self.disconnect()
        self.close_session()

    def execute_command(self, command: str):
        """
        Execute a command into CMaNGOS cli prompt and return the result.

        Send command into CMaNGOS cli prompt and read answered data
        :arg command 'str' to execute
        :return: True on success, False otherwise
        """
        self.wait_cli_prompt()
        logging.info('Execute command : ' + command)
        self.tn_client.write(bytes(command, 'UTF-8'))
        result = str(self.tn_client.read_until(b"mangos>")).replace('\\r', '')  # can remove '\r' char here
        logging.debug('Response ' + result)
        return result

# Account commands -----------------------------------------------------------------------------------------------------

    def get_online_accounts(self):
        """
        Get currently online accounts.

        :return: currently connected account as a dict
        """
        accounts = {}
        result = self.execute_command('account onlinelist \n')
        result = result.split('\\n')[3:-2]
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
        """
        Get account characters as a list.

        :param username: target account login
        :return: account characters as a dict
        """
        characters = {}
        result = self.execute_command('account characters ' + username + ' \n')
        result = result.split('\\n')[3:-2]
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
        """
        Create a new account with a login and a password.

        :param username: new account login
        :param password: new account password
        :return: True on success, False otherwise
        """
        result = self.execute_command('account create ' + username + ' ' + password + ' \n')
        return 'Account with this name already exist' not in result

    def account_set_password(self, username: str, password: str):
        """
        Replace an account password with a new one.

        :param username: target account login
        :param password: new account password
        :return: True on success, False otherwise
        """
        result = self.execute_command('account set password ' + username + ' ' + password + ' ' + password + ' \n')
        return 'The password was changed' in result

    def account_set_addon(self, username: str, addon: int):
        """
        Set expansion access to an account.

        :param username: target account login
        :param addon: expansion id (0, 1, 2 ...)
        :return: True on success, False otherwise
        """
        if addon < 0:
            return False  # wrong value
        result = self.execute_command('account set addon ' + username + ' ' + str(addon) + ' \n')
        return 'has been granted ' + str(addon) + ' expansion rights.' in result

    def account_set_gm_level(self, username: str, gm_level: int):
        """
        Set account permission level.

        :param username: target account login
        :param gm_level: gm level (0: player, 1: moderator, 2: game master, 3: administrator)
        :return: True on success, False otherwise
        """
        if gm_level < 0 or gm_level > 3:
            return False  # wrong value
        result = self.execute_command('account set gmlevel ' + username + ' ' + str(gm_level) + ' \n')
        return 'You change security level of account ' in result

    def account_delete(self, username: str):
        """
        Delete an account.

        :param username: target account login
        :return: True on success, False otherwise
        """
        result = self.execute_command('account delete ' + username + ' \n')
        return 'Account deleted:' in result

    def account_search_from_email(self, user_email: str, limit: int = 100):
        """
        Search in accounts corresponding email (or fragment).

        :param user_email: account email (or a fragment) to search from
        :param limit: result number limit
        :return: found accounts as a map
        """
        accounts = {}
        result = self.execute_command('lookup account email ' + user_email + ' ' + str(limit) + ' \n')
        result = result.split('\\n')[3:-2]
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
        """
        Search in accounts corresponding login (or fragment).

        :param username: account login (or a fragment) to search from
        :param limit: result number limit
        :return: found accounts as a map
        """
        accounts = {}
        result = self.execute_command('lookup account name ' + username + ' ' + str(limit) + ' \n')
        result = result.split('\\n')[3:-2]
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
        """
        Search in accounts corresponding last used ip address (or fragment).

        :param ip_addr: account last used ip address (or a fragment) to search from
        :param limit: result number limit
        :return: found accounts as a map
        """
        accounts = {}
        result = self.execute_command('lookup account ip ' + ip_addr + ' ' + str(limit) + ' \n')
        result = result.split('\\n')[3:-2]
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

    def achievement_details(self, achievement_id: int):
        """
        Get details about an achievement.

        :param achievement_id: the achievement id
        :return: details about the achievement
        """
        result = self.execute_command('achievement ' + str(achievement_id) + ' \n')
        return result  # TODO

    def achievement_search(self, achievement_name: str):
        """
        Search in achievements with a name (or a fragment).

        :param achievement_name: name to lookup (or a fragment)
        :return: list of achievement results
        """
        result = self.execute_command('lookup achievement ' + achievement_name + ' \n')
        return result  # TODO

    def achievement_state(self, character: str, achievement_id: int):
        """
        Get an achievement state for a character.

        :param character: target character
        :param achievement_id: target achievement id
        :return: this achievement state for the target character
        """
        result = self.execute_command('achievement ' + character + ' ' + str(achievement_id) + ' \n')
        return result  # TODO

    def achievement_set_complete(self, character: str, achievement_id: int):
        """
        Set an achievement complete for a character.

        :param character: target character
        :param achievement_id: target achievement id
        :return: True on success, False otherwise
        """
        result = self.execute_command('achievement add ' + character + ' ' + str(achievement_id) + ' \n')
        return result  # TODO

    def achievement_remove(self, character: str, achievement_id: int):
        """
        Reset an achievement for a character.

        :param character: target character
        :param achievement_id: target achievement id
        :return: True on success, False otherwise
        """
        result = self.execute_command('achievement remove ' + character + ' ' + str(achievement_id) + ' \n')
        return result  # TODO

    def achievement_criteria_set_complete_progress(self, character: str, criteria_id: int):
        """
        Set an achievement criteria complete for a character.

        :param character: target character
        :param criteria_id: target achievement criteria id
        :return: True on success, False otherwise
        """
        result = self.execute_command('achievement criteria add ' + character + ' ' + str(criteria_id) + ' \n')
        return result  # TODO

    def achievement_criteria_add_progress(self, character: str, criteria_id: int, change: int):
        """
        Add some progress to an achievement criteria for a character.

        :param character: target character
        :param criteria_id: target achievement criteria id
        :param change: progress state to add
        :return: True on success, False otherwise
        """
        result = self.execute_command('achievement criteria add ' + character +
                                      ' ' + str(criteria_id) + ' ' + str(change) + ' \n')
        return result  # TODO

    def achievement_criteria_reset_progress(self, character: str, criteria_id: int):
        """
        Reset an achievement criteria for a character.

        :param character: target character
        :param criteria_id: target achievement criteria id
        :return: True on success, False otherwise
        """
        result = self.execute_command('achievement criteria remove ' + character + ' ' + str(criteria_id) + ' \n')
        return result  # TODO

    def achievement_criteria_reduce_progress(self, character: str, criteria_id: int, change: int):
        """
        Remove some progress to an achievement criteria for a character.

        :param character: target character
        :param criteria_id: target achievement criteria id
        :param change: progress state to remove
        :return: True on success, False otherwise
        """
        result = self.execute_command('achievement criteria remove ' + character +
                                      ' ' + str(criteria_id) + ' ' + str(change) + ' \n')
        return result  # TODO

# AHBot commands -------------------------------------------------------------------------------------------------------

    def ahbot_reload_conf(self):
        """
        Reload AHBot configuration.

        :return: True if success, False otherwise
        """
        result = self.execute_command('ahbot reload \n')
        return 'All config are reloaded from ahbot configuration file.' in result

    def ahbot_status(self, detailed: bool = False):
        """
        Get AHBot information.

        :param detailed: True for more information
        :return: AHBot information
        """
        command = 'ahbot status '
        if detailed:
            command += 'all '
        command += ' \n'
        result = self.execute_command(command)
        return result  # TODO

    def ahbot_reset_auction(self, force_all_rebuild: bool = False):
        """
        Reset AHBot auctions.

        :param force_all_rebuild: True to force build again all auctions
        :return: True on success, False otherwise
        """
        command = 'ahbot rebuild '
        if force_all_rebuild:
            command += 'all '
        command += ' \n'
        result = self.execute_command(command)
        return result  # TODO

    def ahbot_set_all_quota(self, grey_items: int, white_items: int, green_items: int,
                            blue_items: int, purple_items: int, orange_items: int, yellow_items: int):
        """
        Set AHBot item quotas for auctions.

        :param grey_items: number of grey color items
        :param white_items: number of white color items
        :param green_items: number of green color items
        :param blue_items: number of blue color items
        :param purple_items: number of purple color items
        :param orange_items: number of orange color items
        :param yellow_items: number of yellow color items
        :return: True on success, False otherwise
        """
        result = self.execute_command('ahbot items amount ' + str(grey_items) + ' ' + str(white_items) +
                                      ' ' + str(green_items) + ' ' + str(blue_items) + ' ' + str(purple_items) +
                                      ' ' + str(orange_items) + ' ' + str(yellow_items) + ' \n')
        return result  # TODO

    def ahbot_set_grey_quota(self, grey_items: int):
        """
        Set AHBot quota for grey items.

        :param grey_items: number of grey color items
        :return: True on success, False otherwise
        """
        result = self.execute_command('ahbot items amount grey ' + str(grey_items) + ' \n')
        return result  # TODO

    def ahbot_set_white_quota(self, white_items: int):
        """
        Set AHBot quota for white items.

        :param white_items: number of white color items
        :return: True on success, False otherwise
        """
        result = self.execute_command('ahbot items amount white ' + str(white_items) + ' \n')
        return result  # TODO

    def ahbot_set_green_quota(self, green_items: int):
        """
        Set AHBot quota for green items.

        :param green_items: number of green color items
        :return: True on success, False otherwise
        """
        result = self.execute_command('ahbot items amount green ' + str(green_items) + ' \n')
        return result  # TODO

    def ahbot_set_blue_quota(self, blue_items: int):
        """
        Set AHBot quota for blue items.

        :param blue_items: number of blue color items
        :return: True on success, False otherwise
        """
        result = self.execute_command('ahbot items amount blue ' + str(blue_items) + ' \n')
        return result  # TODO

    def ahbot_set_purple_quota(self, purple_items: int):
        """
        Set AHBot quota for purple items.

        :param purple_items: number of purple color items
        :return: True on success, False otherwise
        """
        result = self.execute_command('ahbot items amount purple ' + str(purple_items) + ' \n')
        return result  # TODO

    def ahbot_set_orange_quota(self, orange_items: int):
        """
        Set AHBot quota for orange items.

        :param orange_items: number of orange color items
        :return: True on success, False otherwise
        """
        result = self.execute_command('ahbot items amount orange ' + str(orange_items) + ' \n')
        return result  # TODO

    def ahbot_set_yellow_quota(self, yellow_items: int):
        """
        Set AHBot quota for yellow items.

        :param yellow_items: number of yellow color items
        :return: True on success, False otherwise
        """
        result = self.execute_command('ahbot items amount yellow ' + str(yellow_items) + ' \n')
        return result  # TODO

    def ahbot_set_ratios(self, alliance_ratio: int, horde_ratio: int, neutral_ratio: int):
        """
        Set AHBot auction ratio for each race.

        :param alliance_ratio: auction ratio for the alliance
        :param horde_ratio: auction ratio for the the horde
        :param neutral_ratio: auction ratio for neutral
        :return: True on success, False otherwise
        """
        result = self.execute_command('ahbot items ratio ' + str(alliance_ratio) +
                                      ' ' + str(horde_ratio) + ' ' + str(neutral_ratio) + ' \n')
        return result  # TODO

    def ahbot_set_alliance_ratio(self, alliance_ratio: int):
        """
        Set AHBot auction ratio for the alliance.

        :param alliance_ratio: auction ratio for the alliance
        :return: True on success, False otherwise
        """
        result = self.execute_command('ahbot items ratio alliance ' + str(alliance_ratio) + ' \n')
        return result  # TODO

    def ahbot_set_horde_ratio(self, horde_ratio: int):
        """
        Set AHBot auction ratio for the horde.

        :param horde_ratio: auction ratio for the horde
        :return: True on success, False otherwise
        """
        result = self.execute_command('ahbot items ratio horde ' + str(horde_ratio) + ' \n')
        return result  # TODO

    def ahbot_set_neutral_ratio(self, neutral_ratio: int):
        """
        Set AHBot auction ratio for neutral.

        :param neutral_ratio: auction ratio for neutral
        :return: True on success, False otherwise
        """
        result = self.execute_command('ahbot items ratio neutral ' + str(neutral_ratio) + ' \n')
        return result  # TODO

# Auction commands -----------------------------------------------------------------------------------------------------

    def auction_show_alliance(self):
        """
        Show alliance auction list.

        :return: alliance auction list
        """
        result = self.execute_command('auction alliance \n')
        return result  # TODO

    def auction_show_horde(self):
        """
        Show horde auction list.

        :return: horde auction list
        """
        result = self.execute_command('auction horde \n')
        return result  # TODO

    def auction_show_goblin(self):
        """
        Show goblin auction list.

        :return: goblin auction list
        """
        result = self.execute_command('auction goblin \n')
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
        return result  # TODO

# Ban commands ---------------------------------------------------------------------------------------------------------

    def ban_account(self, username: str, reason: str, bantime: str = '-1'):
        """
        Ban a player account.

        :param username: target account
        :param reason: ban reason
        :param bantime: ban duration (-1 mean infinite)
        :return: True on success, False otherwise
        """
        result = self.execute_command('ban account ' + username + ' ' + bantime + ' ' + reason + ' \n')
        return result  # TODO

    def ban_character(self, character: str, reason: str, bantime: str = '-1'):
        """
        Ban a player character.

        :param character: target character
        :param reason: ban reason
        :param bantime: ban duration (-1 mean infinite)
        :return: True on success, False otherwise
        """
        result = self.execute_command('ban character ' + character + ' ' + bantime + ' ' + reason + ' \n')
        return result  # TODO

    def ban_ip(self, ip_addr: str, reason: str, bantime: str = '-1'):
        """
        Ban an IP address.

        :param ip_addr: target IP address
        :param reason: ban reason
        :param bantime: ban duration (-1 mean infinite)
        :return: True on success, False otherwise
        """
        result = self.execute_command('ban ip ' + ip_addr + ' ' + bantime + ' ' + reason + ' \n')
        return result  # TODO

    def ban_info_account(self, username: str):
        """
        Show banned account information.

        :param username: target account
        :return: ban information
        """
        result = self.execute_command('baninfo account ' + username + ' \n')
        return result  # TODO

    def ban_info_character(self, character: str):
        """
        Show banned character information.

        :param character: target character
        :return: ban information
        """
        result = self.execute_command('baninfo character ' + character + ' \n')
        return result  # TODO

    def ban_info_ip(self, ip_addr: str):
        """
        Show banned IP address information.

        :param ip_addr: target IP address
        :return: ban information
        """
        result = self.execute_command('baninfo ip ' + ip_addr + ' \n')
        return result  # TODO

    def ban_list_account(self):
        """
        Get banned accoutn list.

        :return: banned account list
        """
        result = self.execute_command('banlist account \n')
        return result  # TODO

    def ban_list_character(self):
        """
        Get banned character list.

        :return: banned character list
        """
        result = self.execute_command('banlist character \n')
        return result  # TODO

    def ban_list_ip(self):
        """
        Get banned IP address list.

        :return: banned IP address list
        """
        result = self.execute_command('banlist ip \n')
        return result  # TODO

    def ban_list_search_account(self, username: str):
        """
        Search a banned account by its name (or a fragment).

        :param username: account name to search (or a fragment)
        :return: result list
        """
        result = self.execute_command('banlist account ' + username + ' \n')
        return result  # TODO

    def ban_list_search_character(self, character: str):
        """
        Search a banned character by its name (or a fragment).

        :param character: character name (or a fragment)
        :return: result list
        """
        result = self.execute_command('banlist character ' + character + ' \n')
        return result  # TODO

    def ban_list_search_ip(self, ip_addr: str):
        """
        Search a banned IP address (or a fragment).

        :param ip_addr: IP address (or a fragment)
        :return: result list
        """
        result = self.execute_command('banlist ip ' + ip_addr + ' \n')
        return result  # TODO

    def unban_account(self, username: str):
        """
        Remove ban to an account.

        :param username: target account
        :return: True on success, False otherwise
        """
        result = self.execute_command('unban account ' + username + ' \n')
        return result  # TODO

    def unban_character(self, character: str):
        """
        Remove ban to a character.

        :param character: target character
        :return: True on success, False otherwise
        """
        result = self.execute_command('unban character ' + character + ' \n')
        return result  # TODO

    def unban_ip(self, ip_addr: str):
        """
        Remove ban to an IP address.

        :param ip_addr: target IP address
        :return: True on success, False otherwise
        """
        result = self.execute_command('unban ip ' + ip_addr + ' \n')
        return result  # TODO

# Character commands ---------------------------------------------------------------------------------------------------

    def character_get_infos(self, character: str):
        """
        Get information about a character.

        :param character: target character
        :return: character information
        """
        result = self.execute_command('pinfo ' + character + ' \n')
        return result  # TODO

    def character_achievements(self, character: str):
        """
        Get character achievement list.

        :param character: target character
        :return: character achievement list
        """
        result = self.execute_command('character achievements ' + character + ' \n')
        return result  # TODO

    def character_customize_at_next_login(self, character: str):
        """
        Open customize menu on next character login.

        It allows the player to modify its character appearance
        :param character: target character
        :return: True on success, False otherwise
        """
        result = self.execute_command('character customize ' + character + ' \n')
        return result  # TODO

    def character_rename_at_next_login(self, character: str):
        """
        Open name menu on next character login.

        It allows the player to modify its character name
        :param character: target character
        :return: True on success, False otherwise
        """
        result = self.execute_command('character rename ' + character + ' \n')
        return result  # TODO

    def character_delete(self, character: str):
        """
        Delete a character.

        :param character: target character
        :return: True on success, Flase otherwise
        """
        result = self.execute_command('character erase ' + character + ' \n')
        return ') deleted' in result

    def character_get_reputation(self, character: str):
        """
        Get a character reputation.

        :param character: target character
        :return: character reputation
        """
        result = self.execute_command('character reputation ' + character + ' \n')
        return result  # TODO

    def character_get_titles(self, character: str):
        """
        Get a character title list.

        :param character: target character
        :return: character title list
        """
        result = self.execute_command('character titles ' + character + ' \n')
        return result  # TODO

    def character_stop_combat(self, character: str):
        """
        Stop combat for a character.

        :param character: target character
        :return: True on success, False otherwise
        """
        result = self.execute_command('combatstop ' + character + ' \n')
        return result  # TODO

    def character_set_level(self, character: str, level: int = 0):
        """
        Set a character level.

        :param character: target character
        :param level: level to set
        :return: True on success, False otherwise
        """
        result = self.execute_command('character level ' + character + ' ' + str(level) + ' \n')
        return result  # TODO

    def character_levelup(self, character: str, level: int = 1):
        """
        Make a character level up.

        :param character: target character
        :param level: number of level
        :return: True on success, False otherwise
        """
        result = self.execute_command('levelup ' + character + ' ' + str(level) + ' \n')
        return result  # TODO

    def character_mute(self, character: str, duration: int = 1):
        """
        Block chat messaging for a character.

        :param character: target character
        :param duration: block duration
        :return: True on success, False otherwise
        """
        result = self.execute_command('mute ' + character + ' ' + str(duration) + ' \n')
        return result  # TODO

    def character_unmute(self, character: str):
        """
        Restore chat messaging for a character.

        :param character: target character
        :return: True on success, False otherwise
        """
        result = self.execute_command('unmute ' + character + ' \n')
        return result  # TODO

    def character_recall(self, character: str):
        """
        Teleport a character to the last safe point.

        :param character: target character
        :return: True on success, False otherwise
        """
        result = self.execute_command('recall ' + character + ' \n')
        return result  # TODO

    def character_restore_deleted(self, character: str, new_name: str = '', account: str = ''):
        """
        Restore a deleted character.

        :param character: target character
        :param new_name: new character name
        :param account: new account to restore into instead of original one
        :return: True on success, False otherwise
        """
        result = self.execute_command('character deleted restore ' + character +
                                      ' ' + new_name + ' ' + account + ' \n')
        return result  # TODO

    def character_delete_deleted(self, character: str):
        """
        Completely delete a deleted character.

        :param character: target character
        :return: True on success, False otherwise
        """
        result = self.execute_command('character deleted delete ' + character + ' \n')
        return result  # TODO

    def character_delete_deleted_old(self):
        """
        Deleted old deleted characters.

        How old value will be read from CMaNGOS server configuration
        :return: True on success, False otherwise
        """
        result = self.execute_command('character deleted old \n')
        return result  # TODO

    def character_delete_deleted_older_than(self, days: int):
        """
        Deleted old deleted characters.

        :param days: how old deleted character will be deleted
        :return: True on success, False otherwise
        """
        result = self.execute_command('character deleted old ' + str(days) + ' \n')
        return result  # TODO

    def character_deleted_list(self):
        """
        Get deleted character list.

        :return: deleted character list
        """
        result = self.execute_command('character deleted list \n')
        return result  # TODO

    def character_search_deleted_list(self, character: str):
        """
        Search a deleted character by its name (or a fragment).

        :param character: name (or a fragment)
        :return: found character list
        """
        result = self.execute_command('character deleted list ' + character + ' \n')
        return result  # TODO

    def character_search_from_name(self, character: str, limit: int = 100):
        """
        Search a character by its name (or a fragment).

        :param character: name (or a fragment)
        :param limit: result limit number
        :return: found character list
        """
        result = self.execute_command('lookup player account ' + character + ' ' + str(limit) + ' \n')
        return result  # TODO

    def character_search_from_email(self, email: str, limit: int = 100):
        """
        Search a character by its email (or a fragment).

        :param email: email (or a fragment)
        :param limit: result limit number
        :return: found character list
        """
        result = self.execute_command('lookup player email ' + email + ' ' + str(limit) + ' \n')
        return result  # TODO

    def character_search_from_ip(self, ip_addr: str, limit: int = 100):
        """
        Search a character by its IP address (or a fragment).

        :param ip_addr: IP address (or a fragment)
        :param limit: result limit number
        :return: found character list
        """
        result = self.execute_command('lookup player ip ' + ip_addr + ' ' + str(limit) + ' \n')
        return result  # TODO

    def character_reset_achievements(self, character: str):
        """
        Reset character achievements.

        :param character: target character
        :return: True on success, False otherwise
        """
        result = self.execute_command('reset achievements ' + character + ' \n')
        return result  # TODO

    def character_reset_honor(self, character: str):
        """
        Reset character honor.

        :param character: target character
        :return: True on success, False otherwise
        """
        result = self.execute_command('reset honor ' + character + ' \n')
        return result  # TODO

    def character_reset_level(self, character: str):
        """
        Reset character level.

        :param character: target character
        :return: True on success, False otherwise
        """
        result = self.execute_command('reset level ' + character + ' \n')
        return result  # TODO

    def character_reset_specs(self, character: str):
        """
        Reset character specs (all talents).

        :param character: target character
        :return: True on success, False otherwise
        """
        result = self.execute_command('reset specs ' + character + ' \n')
        return result  # TODO

    def character_reset_spells(self, character: str):
        """
        Reset character spells.

        :param character: target character
        :return: True on success, False otherwise
        """
        result = self.execute_command('reset spells ' + character + ' \n')
        return result  # TODO

    def character_reset_stats(self, character: str):
        """
        Reset character stats.

        :param character: target character
        :return: True on success, False otherwise
        """
        result = self.execute_command('reset stats ' + character + ' \n')
        return result  # TODO

    def character_reset_talents(self, character: str):
        """
        Reset character talents (current spec).

        :param character: target character
        :return: True on success, False otherwise
        """
        result = self.execute_command('reset talents ' + character + ' \n')
        return result  # TODO

    def character_all_reset_spells(self):
        """
        Reset spells for all characters.

        :return: True on success, False otherwise
        """
        result = self.execute_command('reset all spells \n')
        return result  # TODO

    def character_all_reset_talents(self):
        """
        Reset talents for all characters.

        :return: True on success, False otherwise
        """
        result = self.execute_command('reset all talents \n')
        return result  # TODO

# Debug commands -------------------------------------------------------------------------------------------------------

    def debug_toggle_arenas(self):
        """
        Toggle debug mode for arenas.

        :return: True on success, False otherwise
        """
        result = self.execute_command('debug arena \n')
        return result  # TODO

    def debug_toggle_battlegrounds(self):
        """
        Toggle debug mode for battlegrounds.

        :return: True on success, False otherwise
        """
        result = self.execute_command('debug bg \n')
        return result  # TODO

    def debug_show_spell_coefs(self, spell_id: int):
        """
        Show spell coefficients.

        :param spell_id: target spell
        :return: spell coefficients
        """
        result = self.execute_command('debug spellcoefs ' + str(spell_id) + ' \n')
        return result  # TODO

    def debug_mod_spells(self, spell_mask_bit_index: int, spell_mod_op: int, value: int, pct: bool = False):
        """
        Set debug mod for a spell.

        :param spell_mask_bit_index: target spell
        :param spell_mod_op: spell mod
        :param value: debug value
        :param pct: is it a pct value ?
        :return: True on success, False otherwise
        """
        command = 'debug spellmods '
        if pct:
            command += 'pct '
        else:
            command += 'flat '
        command += str(spell_mask_bit_index) + ' ' + str(spell_mod_op) + ' ' + str(value) + ' \n'
        result = self.execute_command(command)
        return result  # TODO

# Ticket commands ------------------------------------------------------------------------------------------------------

    def ticket_delete_all(self):
        """
        Delete all tickets.

        :return: True on success, False otherwise
        """
        result = self.execute_command('delticket all \n')
        return result  # TODO

    def ticket_delete(self, ticket_id: int):
        """
        Delete a ticket.

        :param ticket_id: target ticket id
        :return: True on success, False otherwise
        """
        result = self.execute_command('delticket ' + str(ticket_id) + ' \n')
        return result  # TODO

    def ticket_delete_from_character(self, character: str):
        """
        Delete all tickets from a character.

        :param character: target character name
        :return: True on success, False otherwise
        """
        result = self.execute_command('delticket ' + character + ' \n')
        return result  # TODO

    def ticket_gm_show_new_directly(self, activated: bool = True):
        """
        Activate or not new ticket direct show.

        :param activated: activation state
        :return: True on success, False otherwise
        """
        command = 'ticket '
        if activated:
            command += 'on'
        else:
            command += 'off '
        command += ' \n'
        result = self.execute_command(command)
        return result  # TODO

    def ticket_show(self, ticket_id: int):
        """
        Get a ticket information.

        :param ticket_id: target ticket id
        :return: ticket information
        """
        result = self.execute_command('ticket ' + str(ticket_id) + ' \n')
        return result  # TODO

    def ticket_show_from_character(self, character: str):
        """
        Get all tickets from a character.

        :param character: target character
        :return: ticket list
        """
        result = self.execute_command('ticket ' + character + ' \n')
        return result  # TODO

    def ticket_respond(self, ticket_id: int, response: str):
        """
        Answer to a ticket.

        :param ticket_id: target ticket id
        :param response: response content
        :return: True on success, False otherwise
        """
        result = self.execute_command('ticket respond ' + str(ticket_id) + ' ' + response + ' \n')
        return result  # TODO

    def ticket_respond_from_character(self, character: str, response: str):
        """
        Answer to character tickets.

        :param character: target character
        :param response: response content
        :return: True on success, False otherwise
        """
        result = self.execute_command('ticket respond ' + character + ' ' + response + ' \n')
        return result  # TODO

# Event commands -------------------------------------------------------------------------------------------------------

    def event_get_details(self, event_id: int):
        # TODO DOC
        result = self.execute_command('event ' + str(event_id) + ' \n')
        return result  # TODO

    def event_list(self):
        # TODO DOC
        result = self.execute_command('event list \n')
        return result  # TODO

    def event_start(self, event_id: int):
        # TODO DOC
        result = self.execute_command('event start ' + str(event_id) + ' \n')
        return result  # TODO

    def event_stop(self, event_id: int):
        # TODO DOC
        result = self.execute_command('event stop ' + str(event_id) + ' \n')
        return result  # TODO

    def event_search(self, event_name: str):
        # TODO DOC
        result = self.execute_command('lookup event ' + str(event_name) + ' \n')
        return result  # TODO

# Guild commands -------------------------------------------------------------------------------------------------------

    def guild_create(self, guild_name: str, guild_leader: str = ''):
        # TODO DOC
        result = self.execute_command('guild create "' + guild_name + '" ' + guild_leader + ' \n')
        return result  # TODO

    def guild_delete(self, guild_name: str):
        # TODO DOC
        result = self.execute_command('guild delete "' + guild_name + '" \n')
        return result  # TODO

    def guild_invite(self, character: str, guild_name: str):
        # TODO DOC
        result = self.execute_command('guild invite ' + character + ' "' + guild_name + '" \n')
        return result  # TODO

    def guild_character_set_rank(self, character: str, rank: int):
        # TODO DOC
        result = self.execute_command('guild rank ' + character + ' ' + str(rank) + ' \n')
        return result  # TODO

    def guild_uninvite(self, character: str):
        # TODO DOC
        result = self.execute_command('guild uninvite ' + character + ' \n')
        return result  # TODO

# Honor commands -------------------------------------------------------------------------------------------------------

    def honor_reset(self, character: str):
        # TODO DOC
        result = self.execute_command('reset honor ' + character + ' \n')
        return result  # TODO

# Learn commands -------------------------------------------------------------------------------------------------------

    def learn_all_default(self, character: str):
        """
        Make a character all its spells learned (race, class and rewards).

        :param character: target character
        :return: True on success, False otherwise
        """
        result = self.execute_command('learn all_default ' + character + ' \n')
        return result  # TODO

    def learn_all_for_gm(self):
        """
        Make all Game Masters all their spells learned (race, class and rewards).

        :return: True on success, False otherwise
        """
        result = self.execute_command('learn all_gm \n')
        return result  # TODO

# Lookup commands ------------------------------------------------------------------------------------------------------

    def area_search(self, area_name: str):
        # TODO DOC
        result = self.execute_command('lookup area ' + area_name + ' \n')
        return result  # TODO

    def creature_search(self, creature_name: str):
        # TODO DOC
        result = self.execute_command('lookup creature ' + creature_name + ' \n')
        return result  # TODO

    def currency_search(self, currency_name: str):
        # TODO DOC
        result = self.execute_command('lookup currency ' + currency_name + ' \n')
        return result  # TODO

    def faction_search(self, faction_name: str):
        # TODO DOC
        result = self.execute_command('lookup faction ' + faction_name + ' \n')
        return result  # TODO

    def item_search(self, item_name: str):
        # TODO DOC
        result = self.execute_command('lookup item ' + item_name + ' \n')
        return result  # TODO

    def itemset_search(self, item_name: str):
        # TODO DOC
        result = self.execute_command('lookup itemset ' + item_name + ' \n')
        return result  # TODO

    def object_search(self, object_name: str):
        # TODO DOC
        result = self.execute_command('lookup object ' + object_name + ' \n')
        return result  # TODO

    def pool_search(self, pool_desc: str):
        # TODO DOC
        result = self.execute_command('lookup pool ' + pool_desc + ' \n')
        return result  # TODO

    def quest_search(self, quest_name: str):
        # TODO DOC
        result = self.execute_command('lookup quest ' + quest_name + ' \n')
        return result  # TODO

    def skill_search(self, skill_name: str):
        # TODO DOC
        result = self.execute_command('lookup skill ' + skill_name + ' \n')
        return result  # TODO

    def spell_search(self, spell_name: str):
        # TODO DOC
        result = self.execute_command('lookup spell ' + spell_name + ' \n')
        return result  # TODO

    def taxinode_search(self, taxinode_name: str):
        # TODO DOC
        result = self.execute_command('lookup taxinode ' + taxinode_name + ' \n')
        return result  # TODO

    def tele_search(self, tele_name: str):
        # TODO DOC
        result = self.execute_command('lookup tele ' + tele_name + ' \n')
        return result  # TODO

    def title_search(self, title_name: str):
        # TODO DOC
        result = self.execute_command('lookup title ' + title_name + ' \n')
        return result  # TODO

# NPC commands ---------------------------------------------------------------------------------------------------------

    def npc_show_ai_info(self):
        """
        Get NPC AI and scripts information.

        :return: NPC AI and scripts information
        """
        result = self.execute_command('npc aiinfo \n')
        return result  # TODO

    def npc_delete(self, npc_id: int):
        """
        Delete a NPC.

        :param npc_id: NPC id to delete
        :return: True on success, False otherwise
        """
        result = self.execute_command('npc delete ' + str(npc_id) + ' \n')
        return result  # TODO

    def npc_set_move_type(self, npc_id: int, stay: bool = False, random: bool = False,  delete_waypoints: bool = False):
        """
        Modify movements from a NPC.

        :param npc_id: target NPC id
        :param stay: make NPC static
        :param random: make NPC movements random
        :param delete_waypoints: want to delete NPC waypoints ?
        :return: True on success, False otherwise
        """
        command = 'npc setmovetype ' + str(npc_id) + ' '
        if stay:
            command += 'stay '  # static
        elif random:
            command += 'random '  # random movement
        else:
            command += 'way '  # follow its waypoints
        if not delete_waypoints:  # don't delete waypoint
            command += 'NODEL '  # keep waypoint
        command += ' \n'
        result = self.execute_command(command)
        return result  # TODO

# Dump commands ------------------------------------------------------------------------------------------------------

    def dump_character_import(self, dump_file: str, account_name: str, new_id: int, character_name: str):
        """
        Import a character from a dump file

        :param dump_file: file name to import from
        :param account_name: account to import into
        :param new_id: new id for the imported character
        :param character_name: name for the imported character
        :return: True on import success
        """
        result = self.execute_command('pdump load ' + dump_file + ' ' + account_name +
                                      ' ' + character_name + ' ' + str(new_id) + ' \n')
        return 'Character loaded successfully!' in result

    def dump_character_export(self, dump_file: str, character: str):
        """
        Export a character to a dump file.

        :param dump_file: export file name
        :param character: character name to export
        :return: True on export success
        """
        result = self.execute_command('pdump write ' + dump_file + ' ' + character + ' \n')
        return 'Character dumped successfully!' in result

# Send commands --------------------------------------------------------------------------------------------------------

    def send_mail(self, character: str, subject: str = '', message: str = ''):
        """
        Send an ingame mail to a character.

        :param character: target character
        :param subject: ingame mail subject
        :param message: ingame mail content
        :return: True on success, False otherwise
        """
        result = self.execute_command('send mail ' + character + ' "' + subject + '" "' + message + '" \n')
        return 'Mail sent to ' in result

    def send_mass_mail(self, mask: str, subject: str = '', message: str = ''):
        """
        Send an ingame mail to many characters.

        :param mask: character name mask to target
        :param subject: ingame mail subject
        :param message: ingame mail content
        :return: True on success, False otherwise
        """
        result = self.execute_command('send mass mail ' + mask + ' "' + subject + '" "' + message + '" \n')
        return 'Mail sent to ' in result

    def send_money(self, character: str, money: int, subject: str = '', message: str = ''):
        """
        Send an ingame mail with money attached to a character.

        :param character: target character
        :param money: money amount to send
        :param subject: ingame mail subject
        :param message: ingame mail content
        :return: True on success, False otherwise
        """
        result = self.execute_command('send money ' + character +
                                      ' "' + subject + '" "' + message + '" ' + str(money) + ' \n')
        return 'Mail sent to ' in result

    def send_mass_money(self, mask: str, money: int, subject: str = '', message: str = ''):
        """
        Send an ingame mail with money attached to many characters.

        :param mask: character name mask to target
        :param money: money amount to send
        :param subject: ingame mail subject
        :param message: ingame mail content
        :return: True on success, False otherwise
        """
        result = self.execute_command('send mass money ' + mask +
                                      ' "' + subject + '" "' + message + '" ' + str(money) + ' \n')
        return 'Mail sent to ' in result

    def send_items(self, character: str, items: dict, subject: str = '', message: str = ''):
        """
        Send an ingame mail with one or more objects attached to a character.

        :param character: target character
        :param items: object(s) to send
        :param subject: ingame mail subject
        :param message: ingame mail content
        :return: True on success, False otherwise
        """
        command = 'send items ' + character + ' "' + subject + '" "' + message + '"'
        for item in items:
            command += ' ' + str(item) + ':' + str(items[item])
        command += ' \n'
        result = self.execute_command(command)
        return 'Mail sent to ' in result

    def send_mass_items(self, mask: str, items: dict, subject: str = '', message: str = ''):
        """
        Send an ingame mail with one or more objects attached to many characters.

        :param mask: character name mask to target
        :param items: object(s) to send
        :param subject: ingame mail subject
        :param message: ingame mail content
        :return: True on success, False otherwise
        """
        command = 'send mass items ' + mask + ' "' + subject + '" "' + message + '"'
        for item in items:
            command += ' ' + str(item) + ':' + str(items[item])
        command += ' \n'
        result = self.execute_command(command)
        return 'Mail sent to ' in result

    def send_announce(self, message: str):
        """
        Send a announce to all online players.

        It'll be displayed in the chat box
        :param message: message to announce to all online players
        """
        self.execute_command('announce ' + message + ' \n')

    def send_notification(self, message: str):
        """
        Notify all online players.

        It'll be displayed on the top of the screen
        :param message: message to notify to all online players
        """
        self.execute_command('notify ' + message + ' \n')

    def send_message(self, character: str, message: str = ''):
        """
        Send a announce to a character (online player).

        It'll be displayed in the chat box
        :param character: target online character
        :param message: message to announce at this player
        """
        self.execute_command('send message ' + character + ' "' + message + '" \n')

# Server commands ------------------------------------------------------------------------------------------------------

# TODO

    def server_save_all(self):
        # TODO DOC
        result = self.execute_command('saveall \n')
        return result  # TODO

    def server_idle_restart(self, delay: int = 1):
        # TODO DOC
        result = self.execute_command('server idlerestart ' + str(delay) + ' \n')
        return result  # TODO

    def server_cancel_idle_restart(self):
        # TODO DOC
        result = self.execute_command('server idlerestart cancel \n')
        return result  # TODO

    def server_idle_shutdown(self, delay: int = 1):
        # TODO DOC
        result = self.execute_command('server idleshutdown ' + str(delay) + ' \n')
        return result  # TODO

    def server_cancel_idle_shutdown(self):
        # TODO DOC
        result = self.execute_command('server idleshutdown cancel \n')
        return result  # TODO

    def server_get_infos(self):
        # TODO DOC
        result = self.execute_command('server info \n')
        return result  # TODO

    def server_get_log_filter(self):
        # TODO DOC
        result = self.execute_command('server log filter \n')
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
        return result  # TODO

    def server_get_log_level(self):
        # TODO DOC
        result = self.execute_command('server log level \n')
        return result  # TODO

    def server_set_log_level(self, log_level: int):
        # TODO DOC
        result = self.execute_command('server log level ' + str(log_level) + ' \n')
        return result  # TODO

    def server_get_motd(self):
        # TODO DOC
        result = self.execute_command('server motd \n')
        return result  # TODO

    def server_set_motd(self, message: str):
        # TODO DOC
        result = self.execute_command('server set motd ' + message + ' \n')
        return result  # TODO

    def server_restart(self, delay: int):
        # TODO DOC
        result = self.execute_command('server restart ' + str(delay) + ' \n')
        return result  # TODO

    def server_cancel_restart(self):
        # TODO DOC
        result = self.execute_command('server restart cancel \n')
        return result  # TODO

    def server_exit(self):
        # TODO DOC
        result = self.execute_command('server exit \n')
        return result  # TODO

    def server_shutdown(self, delay: int):
        # TODO DOC
        result = self.execute_command('server shutdown ' + str(delay) + ' \n')
        return result  # TODO

    def server_cancel_shutdown(self):
        # TODO DOC
        result = self.execute_command('server shutdown cancel \n')
        return result  # TODO

    def server_check_expired_corpses(self):
        # TODO DOC
        result = self.execute_command('server corpses \n')
        return result  # TODO

    def server_reload_config(self):
        # TODO DOC
        result = self.execute_command('reload config \n')
        return result  # TODO

    def server_reload_all(self):
        # TODO DOC
        result = self.execute_command('reload all \n')
        return result  # TODO

    def server_reload_achievements(self):
        # TODO DOC
        result = self.execute_command('reload all_achievement \n')
        return result  # TODO

    def server_reload_areas(self):
        # TODO DOC
        result = self.execute_command('reload all_area \n')
        return result  # TODO

    def server_reload_eventais(self):
        # TODO DOC
        result = self.execute_command('reload all_eventai \n')
        return result  # TODO

    def server_reload_items(self):
        # TODO DOC
        result = self.execute_command('reload all_item \n')
        return result  # TODO

    def server_reload_locales(self):
        # TODO DOC
        result = self.execute_command('reload all_locales \n')
        return result  # TODO

    def server_reload_loots(self):
        # TODO DOC
        result = self.execute_command('reload all_loot \n')
        return result  # TODO

    def server_reload_npcs(self):
        # TODO DOC
        result = self.execute_command('reload all_npc \n')
        return result  # TODO

    def server_reload_quests(self):
        # TODO DOC
        result = self.execute_command('reload all_quest \n')
        return result  # TODO

    def server_reload_scripts(self):
        # TODO DOC
        result = self.execute_command('reload all_script \n')
        return result  # TODO

    def server_reload_spells(self):
        # TODO DOC
        result = self.execute_command('reload all_spell \n')
        return result  # TODO

    def server_show_player_limits(self):
        # TODO DOC
        result = self.execute_command('server plimit \n')
        return result  # TODO

    def server_set_player_number_limit(self, number: int):
        # TODO DOC
        result = self.execute_command('server plimit ' + str(number) + ' \n')
        return result  # TODO

    def server_set_player_restrict_limit(self):
        # TODO DOC
        result = self.execute_command('server plimit player \n')
        return result  # TODO

    def server_set_moderator_restrict_limit(self):
        # TODO DOC
        result = self.execute_command('server plimit moderator \n')
        return result  # TODO

    def server_set_gamemaster_restrict_limit(self):
        # TODO DOC
        result = self.execute_command('server plimit gamemaster \n')
        return result  # TODO

    def server_set_administrator_restrict_limit(self):
        # TODO DOC
        result = self.execute_command('server plimit administrator \n')
        return result  # TODO

    def server_reset_player_limits(self):
        # TODO DOC
        result = self.execute_command('server plimit reset \n')
        return result  # TODO

    def server_load_scripts(self, script_library_name: str):
        # TODO DOC
        result = self.execute_command('loadscripts ' + script_library_name + ' \n')
        return result  # TODO

# Gobject commands -----------------------------------------------------------------------------------------------------

# TODO

    def gobject_add(self, gobject_id: int, spawn_time: int):
        # TODO DOC
        result = self.execute_command('gobject add ' + str(gobject_id) + ' ' + str(spawn_time) + ' \n')
        return result  # TODO

    def gobject_delete(self, gobject_id: int):
        # TODO DOC
        result = self.execute_command('gobject delete ' + str(gobject_id) + ' \n')
        return result  # TODO

    def gobject_move(self, gobject_id: int, x_pos: int, y_pos: int, z_pos: int):
        # TODO DOC
        result = self.execute_command('gobject move ' + str(gobject_id) +
                                      ' ' + str(x_pos) + ' ' + str(y_pos) + ' ' + str(z_pos) + ' \n')
        return result  # TODO

    def gobject_turn(self, gobject_id: int, z_angle: int):
        # TODO DOC
        result = self.execute_command('gobject turn ' + str(gobject_id) + ' ' + str(z_angle) + ' \n')
        return result  # TODO

    def gobject_set_phase_mask(self, gobject_id: int, phasemask: int):
        # TODO DOC
        result = self.execute_command('gobject setphase ' + str(gobject_id) + ' ' + str(phasemask) + ' \n')
        return result  # TODO

    def gobject_get_location(self, gobject_id: int):
        # TODO DOC
        result = self.execute_command('gobject target ' + str(gobject_id) + ' \n')
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
        return result  # TODO

    def gm_get_gm_mode(self):
        result = self.execute_command('gm \n')
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
        return result  # TODO

    def gm_get_gm_mode_chat(self):
        result = self.execute_command('gm chat \n')
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
        return result  # TODO

    def gm_all_list(self):
        # TODO DOC
        result = self.execute_command('gm list \n')
        return result  # TODO

    def gm_ingame_list(self):
        # TODO DOC
        result = self.execute_command('gm ingame \n')
        return result  # TODO

# Various commands -----------------------------------------------------------------------------------------------------

# TODO

    def list_all_talents(self):
        # TODO DOC
        result = self.execute_command('list talents \n')
        return result  # TODO

    def list_objects(self, object_id: int, limit: int = 10):
        # TODO DOC
        result = self.execute_command('list object ' + str(object_id) + ' ' + str(limit) + ' \n')
        return result  # TODO

    def list_items(self, item_id: int, limit: int = 10):
        # TODO DOC
        result = self.execute_command('list item ' + str(item_id) + ' ' + str(limit) + ' \n')
        return result  # TODO

    def list_creatures(self, creature_id: int, limit: int = 10):
        # TODO DOC
        result = self.execute_command('list item ' + str(creature_id) + ' ' + str(limit) + ' \n')
        return result  # TODO

    def pool_get_infos(self, pool_id: int):
        # TODO DOC
        result = self.execute_command('pool ' + str(pool_id) + ' \n')
        return result  # TODO

    def pool_get_list_spawned(self, pool_id: int):
        # TODO DOC
        result = self.execute_command('pool spawns ' + str(pool_id) + ' \n')
        return result  # TODO

    def title_set_mask(self, title_mask: str):
        # TODO DOC
        result = self.execute_command('titles setmask ' + title_mask + ' \n')
        return result  # TODO

    def tele_delete(self, tele_name: str):
        # TODO DOC
        result = self.execute_command('tele del ' + tele_name + ' \n')
        return result  # TODO

    def tele_character(self, tele_name: str, character: str):
        # TODO DOC
        result = self.execute_command('tele name ' + character + ' ' + tele_name + ' \n')
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
        return result  # TODO

    def kick_character(self, character: str):
        # TODO DOC
        result = self.execute_command('kick ' + character + ' \n')
        return result  # TODO

    def instance_get_infos(self):
        # TODO DOC
        result = self.execute_command('instance stats \n')
        return result  # TODO

    def arena_point_flush(self):
        # TODO DOC
        result = self.execute_command('flusharenapoints \n')
        return result  # TODO


# Test zone :
tn = TelnetWrapper(host='10.0.0.125', port='3443', user='administrator', pwd='administrator')

tn.character_get_infos('Petroska')

print(tn.ahbot_status(True))

tn.close()
