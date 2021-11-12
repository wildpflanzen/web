import os
import re
import codecs

htmlfiles = [f for f in os.listdir('.') if os.path.splitext(f)[1].lower() == '.html']
for file in htmlfiles:
    if file[:6] == 'index-':
        continue
    if file in ['cookies.html', 'error-404.html',
                'impressum.html', 'kontakt.html',
                'index.html', 'systematik.html',
                'trachtpflanzen.html']:
        continue
    print(file)
    data = codecs.open(file, 'r', encoding='utf-8').read()
    database = re.split('\<\!\-\- Database|Database [end ]+\-\-\>', data)[1]
    database = database.split('\n')[2:-1]
    database = [line[3:] for line in database]
    
    newfile = os.path.splitext(file)[0] + '.txt'
    codecs.open(newfile, 'w', encoding='utf-8').write('\n'.join(database))

