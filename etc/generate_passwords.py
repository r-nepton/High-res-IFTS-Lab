# This function generates passwords for the cryo-server. The random password
# is stored in the "secret.password" file, in the /etc directory.
import os, random, string, json

length = 10
chars = 'AABCDEEEEEFFFGHIIIJKKKLMMNOPPQRSTUUUVWXYYZ1234567890'
random.seed = (os.urandom(1024))

password = ''.join(random.choice(chars) for i in range(length))

database = { "password": password }

f = open('secret.passwords', 'w')
f.write( json.dumps(database) )
f.close()

print "I'm updating the password file."
print "Your password is:", password
print "Password file updated."