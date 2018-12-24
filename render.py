import os
import re
import codecs
from jinja2 import Environment, FileSystemLoader, Template
import yaml
import subprocess
import shutil


def main():
   # Read database
   print('\n\nReading data ...')
   database = read_path('source')

   # Test database errors
   test_errors(database)

   # Make thumbnails
   make_thumbnails(database)

   # Make species html pages
   make_html_index(database)
   make_html_species(database)
   make_html_main(database)


def make_html_main(database):

   # Setup Jinja environment
   jinja_env = Environment( loader=FileSystemLoader(searchpath='templates') )
   jinja_env.globals['database'] = database
   html_template = jinja_env.get_template('main-de.html')
   
   # Make html main file
   filename = os.path.join('docs', 'index.html')
   print('   %s' % filename)
   html = html_template.render(groups=database['groups'])
   with codecs.open(filename, 'w', encoding='utf-8-sig') as fo:
      fo.write(html)


def make_html_index(database):
   print('\n\nRendering html index pages ...')

   # Setup Jinja environment
   jinja_env = Environment( loader=FileSystemLoader(searchpath='templates') )
   jinja_env.globals['database'] = database
   html_template = jinja_env.get_template('index-de.html')

   # Make html index files
   for group_path, group in database['groups'].items():
      filename = os.path.join('docs', group['name'] + '.html')
      print('   %s' % filename)
      html = html_template.render(group=group)
      with codecs.open(filename, 'w', encoding='utf-8-sig') as fo:
         fo.write(html)


def make_html_species(database):
   print('\n\nRendering html pages ...')

   # Setup Jinja environment
   jinja_env = Environment( loader=FileSystemLoader(searchpath='templates') )
   jinja_env.globals['database'] = database
   html_template = jinja_env.get_template('species-de.html')

   # Make html files
   filenames = []
   for register in database['species']:
      filename = os.path.join('docs', register['name'] + '.html')
      if filename in filenames:
         print('   Error: duplicated html %s' % filename)
         continue
      elif not os.path.isfile(filename):
         print('   %s' % filename)
         filenames.append(filename)
         html = html_template.render(register=register)
         with codecs.open(filename, 'w', encoding='utf-8-sig') as fo:
            fo.write(html)


def test_file(register, file):
   filename = os.path.join(register['path'], file)
   if not os.path.isfile(filename):
      print("   Error, doesn't exitst: %s" % filename)
      return None
   return filename


def test_errors(database):
   print('\n\nFinding errors ...')

   # Test image files
   names = []
   for register in database['species']:
      # Test species names
      if register['name'] in names:
         print('   Duplicated name: %s' + register['name'])
      names.append(register['name'])

      # Test if database images exists
      images = []
      for session in register['sessions']:
         for image in session['images']:
            if test_file(register, image):
               images.append(image)
      if 'thumb' in register:
         if test_file(register, image):
            images.append(image)

      # Test if image files are in database
      for file in os.listdir(register['path']):
         if file[-4:].lower() == '.jpg' and file not in images:
               print('   Error, not in database: %s' % file)
      
      # Link species with group
      group_path = register['group_path']
      if not group_path in database['groups']:
         print('   species without group: %s' % register['path'])
         continue
      group = database['groups'][group_path]
      if not register in group['species']:
          group['species'].append(register)
          register['group'] = group
      else:
         print('   duplicated species: %s' % group_path)


def image_name(register, imagename, session=None):
   thumbname = register['name'] + '-' + re.sub('[^0-9]', '', imagename) + '.jpg'
   if session:
      if not 'thumbs' in session:
         session['thumbs'] = []
      if thumbname in session['thumbs']:
         print('   Error, duplicated image: %s' % os.path.join(reg['path'], thumbname))
      else:
         session['thumbs'].append(thumbname)
   return thumbname


def make_thumbnails(database):
   print('\n\nMaking thumbnails ...')
   thumbfiles = {}
   for register in database['species']:
      for session in register['sessions']:
         for i, image in enumerate(session['images']):
            # Add relative path
            thumbname = image_name(register, image, session)
            source_in = os.path.join(register['path'], image)
            image_out = os.path.join('docs', 'images', thumbname)
            thumb_out = os.path.join('docs', 'thumbs', thumbname)

            # Make thumbnail without overwrite
            if not os.path.isfile(thumb_out):
               if i == 0:
                  thumbnail(source_in, thumb_out, size='360x240')
               else:
                  thumbnail(source_in, thumb_out, size='360x240')

            # Copy image without overwrite
            if not os.path.isfile(image_out):
               shutil.copy2(source_in, image_out)

      # Add main thumbnail if doesn't exists
      if not 'thumb' in register:
         register['thumb'] = register['sessions'][0]['thumbs'][0]
      else:
         register['thumb'] = image_name(register, register['thumb'])


def thumbnail(filein, thumb, size='320x240'):
   print('   Thumbnail: ' + thumb)
   imagemagick = '/bin/imagemagick/convert.exe'
   options = '-quality 88 -thumbnail %s -unsharp 0x.5' % size
   command = imagemagick + ' ' + filein + ' ' + options + ' ' + thumb
   subprocess.call(command, shell=True)


def write(path, fname, data):
   make_dir(path)
   fullname = os.path.join(path, fname)
   with codecs.open(fullname, 'w', encoding='utf-8-sig') as fo:
      fo.write(data)
      print('   ' + fullname)


def make_dir(path):
   subdirs = re.split('/', re.sub(r'\\', '/', path))
   addpath = ''
   for subdir in subdirs:
      addpath = os.path.join(addpath, subdir)
      if not os.path.exists(addpath):
         os.mkdir(addpath)


def read_path(path, database=None):
   if not database:
      database = {'groups':{}, 'species': []}

   # Process files
   index = False
   fnames = os.listdir(path)
   for f in fnames:
      if f.lower() == 'index.txt':
         index = True
         read_data(os.path.join(path, f), database)
   if not index:
      print('   Error, path without index: ' + path)
      
   # Recurse subdirs
   for f in fnames:
      fullname = os.path.join(path, f)
      if os.path.isdir(fullname):
         read_path(fullname, database)

   # Return data
   return database


def species_name(register):
   # Generate species name
   if 'genus' in register and 'species' in register:
      name = register['genus'] + '-' +  register['species']
      name = re.sub('[^a-zA-Z]', '-', name)
      name = re.sub('-+', '-', name).lower()
      return name.lower()
   else:
      print('   Error, missing genus or species in database: %s' % register['path'])
      return ''


def read_data(fname, database):
   # Test if data file
   path, file = os.path.split(fname)
   if file != 'index.txt':
      return
   path = os.path.normpath(path)
   splitpath = path.split(os.sep)[1:]


   # Read data
   #print('Reading: ' + fname)
   with codecs.open(fname, 'r', encoding='utf-8-sig') as fi:
      data = fi.read()
   docs =  [d for d in yaml.load_all(data)]
   register = docs[0]

   # Add group and path
   register['path'] = path

   if 'group_desc' in register:
      # Generate group unique name
      name = re.sub(' ', '', '-'.join(splitpath))
      name = re.sub('_|--', '-', name).lower()
      register['name'] = name
      
      # Group path
      group_path = '/'.join(splitpath)
      register['group_path'] = group_path
      
      # Add group species list
      register['species'] = []
      database['groups'][group_path] = register

   else:
      # Generate species unique name
      register['name'] = species_name(register)

      # Group path
      register['group_path'] = '/'.join(splitpath[:-1])

      # Add photo sessions
      register['sessions'] = [s for s in docs[1:]]
      database['species'].append(register)


main()
