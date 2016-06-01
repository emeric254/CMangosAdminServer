
import xmlrpc.client
import zeep
import zeep.wsse.username

login = 'administrator'
password = 'administrator'
host = '10.0.0.125'
port = '7878'
path = 'urn:MaNGOS'

# with xmlrpc.client.ServerProxy(uri='http://' + login + ':' + password + '@' + host + ':' + port + '/' + path + '/') as soapclient:
#     print(soapclient)
#     print(soapclient.system.listMethods())
#     print(soapclient.executeCommand({'command': 'account onlinelist'}))

# zeep.Client(wsdl='http://' + host + ':' + port + '/' + path, wsse=zeep.wsse.username.UsernameToken(login, password))
