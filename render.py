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

   # Make blume html pages
   make_html_index(database)
   return
   make_html(database)


def make_html_index(database):
   print('\n\nRendering html index pages ...')

   # Setup Jinja environment
   jinja_env = Environment( loader=FileSystemLoader(searchpath='templates') )
   jinja_env.globals['database'] = database
   html_template = jinja_env.get_template('index-de.html')

   # Make html index files
   groups = extract_groups(database)
   for group in groups:
      filename = os.path.join('docs', group + '.html')
      print('   %s' % filename)
      html = html_template.render(group=groups[group])
      with codecs.open(filename, 'w', encoding='utf-8-sig') as fo:
         fo.write(html)


def extract_groups(database):
   groups = {}

   # Extract groups
   for species in database:
      groupname = '-'.join(species['group'])
      if not groupname in groups:
         groups[groupname] = [species]
      else:
         groups[groupname].append(species)
  
   return groups


def make_html(database):
   print('\n\nRendering html pages ...')

   # Setup Jinja environment
   jinja_env = Environment( loader=FileSystemLoader(searchpath='templates') )
   jinja_env.globals['database'] = database
   html_template = jinja_env.get_template('blume-de.html')

   counter = 0
   # Make html files
   filenames = []
   for blume in database:
      counter += 1
      if counter > 5: return
      filename = blume['species'] + '-' +  blume['genus'] + '.html'
      filename = re.sub(' ', '-', filename).lower()
      filename = os.path.join('docs', filename)
      if filename in filenames:
         print('   Error: duplicated html %s' % filename)
         continue
      elif not os.path.isfile(filename):
         print('   %s' % filename)
         filenames.append(filename)
         html = html_template.render(blume=blume)
         with codecs.open(filename, 'w', encoding='utf-8-sig') as fo:
            fo.write(html)


def test_errors(database):
   print('\n\nFinding errors ...')

   # Test if exists database image files
   for reg in database:
      imagefiles = []
      # Test if database images exists
      for session in reg['sessions']:
         for image in session['images']:
            imagefile = os.path.join(reg['path'], image)
            if not os.path.isfile(imagefile):
               print("   Error, doesn't exitst: %s" % imagefile)
            else:
               imagefiles.append(imagefile)

      # Test if image files are in database
      for file in os.listdir(reg['path']):
         if os.path.splitext(file)[1] == '.jpg':
            file = os.path.join(reg['path'], file)
            if not file in imagefiles:
               print('   Error, not in database: %s' % file)


def make_thumbnails(database):
   print('\n\nMaking thumbnails ...')
   thumbfiles = {}
   for reg in database:
      for session in reg['sessions']:
         session['thumbs'] = []
         for i in range(len(session['images'])):
            # Full thumbnail and image names
            imagename = session['images'][i]
            thumbname = reg['name'] + '-' + re.sub('[^0-9]', '', imagename) + '.jpg'
            if thumbname in session['thumbs']:
               print('   Error, duplicated image: %s' % os.path.join(reg['path'], thumbname))
               continue
            session['thumbs'].append(thumbname)

            # Add relative path
            source_in = os.path.join(reg['path'], imagename)
            image_out = os.path.join('docs', 'images', thumbname)
            thumb_out = os.path.join('docs', 'thumbs', thumbname)

            # Don't overwrite thumbnails
            if not os.path.isfile(thumb_out):
               if i == 0:
                  thumbnail(source_in, thumb_out, size='320x240')
               else:
                  thumbnail(source_in, thumb_out, size='320x240')

            if not os.path.isfile(image_out):
               shutil.copy2(source_in, image_out)

      # Add main thumbnail if doesn't exists
      if not 'thumb' in reg:
         reg['thumb'] = reg['sessions'][0]['thumbs'][0]



def thumbnail(filein, thumb, size='320x240'):
   print('   Thumbnail: ' + thumb)
   imagemagick = '/bin/imagemagick/convert.exe'
   options = '-strip -resize %s -interlace Plane -gaussian-blur 0.05 -quality 85' % size
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


def read_path(path):
   database = []

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
         database = database + read_path(fullname)

   # Return data
   return database



def read_data(fname, database):
   # Test if data file
   path, file = os.path.split(fname)
   if not file == 'index.txt':
      return

   # Read data
   #print('Reading: ' + fname)
   with codecs.open(fname, 'r', encoding='utf-8-sig') as fi:
      data = fi.read()
   docs =  [d for d in yaml.load_all(data)]
   register = docs[0]

   # Add group and path
   path = os.path.normpath(path)
   splitpath = path.split(os.sep)
   register['group'] =splitpath[1:-1]
   register['name'] = re.sub('[_ \+]', '-', splitpath[-1]).lower()
   register['path'] = path
   register['database'] = fname

   # Add photo sessions
   register['sessions'] = [s for s in docs[1:]]
   database.append(register)



main()
