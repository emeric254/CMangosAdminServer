#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
from tools import confLoader
from core import server
from tornado import web, escape
from core.APIHandler import APIHandler

# app's title
__title__ = 'RaspberryPhishAdminServer'

logging.basicConfig(filename='../logs/CMangosAdminServer.log', level=logging.INFO)

(
    https_port,
    login,
    password,
    cookie_secret,
    debug,
    autoreload,
    max_attemps,
    blocked_duration
) = confLoader.load_web_server_conf(conf_file='configuration.conf')


class LoginHandler(server.BaseHandler):
    """Handle user login actions
    """
    def get(self):
        """Get login form
        """
        incorrect = self.get_secure_cookie('incorrect')
        if incorrect and int(incorrect) >= max_attemps:
            logging.warning('an user already blocked')
            self.clear_cookie('user')
            self.render('blocked.html', blocked_duration=blocked_duration)
            return
        self.render('login.html', failed=False)

    def post(self):
        """Post connection form and try to connect with these credentials
        """
        incorrect = self.get_secure_cookie('incorrect')
        if not incorrect or int(incorrect) < 0:
            incorrect = 0
        elif int(incorrect) >= max_attemps:
            logging.warning('an user is blocked')
            self.clear_cookie('user')
            self.render('blocked.html', blocked_duration=blocked_duration)
            return
        getusername = escape.xhtml_escape(self.get_argument('username'))
        getpassword = escape.xhtml_escape(self.get_argument('password'))
        if login == getusername and password == getpassword:
            logging.info('right credentials')
            self.set_secure_cookie('user', self.get_argument('username'), expires_days=1)
            self.clear_cookie('incorrect')
            self.redirect('/')
        else:
            logging.info('invalid credentials')
            incorrect = int(incorrect) + 1
            self.set_secure_cookie('incorrect', str(incorrect), expires_days=blocked_duration)
            if incorrect >= max_attemps:
                logging.warning('an user is now blocked')
                self.clear_cookie('user')
                self.render('blocked.html', blocked_duration=blocked_duration)
            else:
                self.render('login.html', failed=True)


class LogoutHandler(server.BaseHandler):
    """Handle user logout action
    """
    def get(self):
        """Disconnect an user, delete his cookie and redirect him
        """
        self.clear_cookie('user')
        self.redirect('/')


class MainPageHandler(server.BaseHandler):
    """Handle main page requests

    it require an authenticated user
    GET method give the static page
    """
    @web.authenticated
    async def get(self):
        """Render main page
        """
        self.render('./index.html')


def main():
    """Main function, define an Application and start server instances with it.
    """
    # define app settings
    settings = {
        'static_path': './static',
        'template_path': './templates',
        'cookie_secret': cookie_secret,
        'xsrf_cookies': True,
        'login_url': '/login',
        'debug': debug,
        'autoreload': autoreload
    }
    # define Application endpoints
    application = web.Application([
            (r'/login', LoginHandler),
            (r'/logout', LogoutHandler),
            (r'/api/(.*)$', APIHandler),
            (r'/', MainPageHandler)
        ], **settings)
    # start a server running this Application with these loaded parameters
    server.start_server(application, https_port=https_port)


if __name__ == '__main__':
    main()  # execute main function
