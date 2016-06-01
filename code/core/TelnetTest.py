
import telnetlib

serverip = '10.0.0.125'
port = '3443'
user = 'administrator'
password = 'administrator'

# ----------------------------------------------------------------------------------------------------------------------

tn = telnetlib.Telnet(host=serverip, port=port)
print('Telnet client connected to ', tn.host, tn.port)

# ----------------------------------------------------------------------------------------------------------------------

tn.read_until(b"Username:")
tn.write(user.encode('ascii') + b" \n")
if password:
    tn.read_until(b"Password:")
    tn.write(password.encode('ascii') + b" \n")
print('successfully connected as ', user)

# logged in succesfully !
# ----------------------------------------------------------------------------------------------------------------------

print(tn.read_until(b"mangos>"))

# waiting for cli prompt
# ----------------------------------------------------------------------------------------------------------------------

print('\n', 'connected account list', '\n')
tn.write(b"account onlinelist \n")

result = str(tn.read_until(b"mangos>"))
result = result.replace('\\r', '').split('\\n')[3:-2]
for account in result:
    print(account)

# ----------------------------------------------------------------------------------------------------------------------

print('\n', 'available command list', '\n')
tn.write(b"commands \n")

result = str(tn.read_until(b"mangos>"))
result = result.replace('\\r', '').split('\\n')[2:-1]
for command in result:
    print(command)


# ----------------------------------------------------------------------------------------------------------------------

print('Disconnecting from current session')
tn.write(b"quit \n")

# ----------------------------------------------------------------------------------------------------------------------

print('Close telnet connection')
tn.close()
