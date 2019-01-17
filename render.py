"""
   Static web generator for image files.

   ----------------------------------------------------------------

   :copyright: (c) 2018 by Carlos Pardo
   :license: GPL v3  <https://www.gnu.org/licenses/gpl-3.0.html>

   This program is free software; you can redistribute it and/or
   modify it under the terms of the GNU General Public License
   version 3 as published by the Free Software Foundation.
"""

import os
import re
import codecs
from jinja2 import Environment, FileSystemLoader, Template
import yaml
import subprocess
import shutil
from collections import UserDict

global options


def main():

   # Read options
   global options
   read_options('options.ini')

   # Read database
   print('\nReading data ...')
   database = Database()
   database.read('source')

   # Make thumbnails
   make_thumbnails(database)

   # Make html pages
   generator = HTML_generator(database)
   generator.overwrite = True

   # Copy static files
   generator.copy_static()

   # Generate html files
   generator.html_species()
   generator.html_groups()
   generator.html_index()
   generator.html_extra()

   
   # End
   print('\nRender end.\n')


# --------------------------------------------------------------------
#    HTML RENDERING
# --------------------------------------------------------------------
class HTML_generator():

   def __init__(self, database):
      self.database = database
      self.overwrite = False
      self.verbose = True

   def copy_static(self):
      print("Copying static files ...")
      self.copy_files('source/static', 'docs/static')
      self.copy_files('templates/root', 'docs')
      self.copy_files('templates/static', 'docs/static')     


   def copy_files(self, src, dst):
      if not os.path.isdir(src):
         return
      if not os.path.isdir(dst):
         os.mkdir(dst)
      for fname in os.listdir(src):
         if self.overwrite or not os.path.isfile(os.path.join(dst, fname)):
            shutil.copy2(os.path.join(src, fname), os.path.join(dst, fname))


   def html_extra(self):
      print('\nRendering html extra ...')
      path = 'templates/extra'
      extra = [f for f in os.listdir(path) if f[-5:].lower() == '.html']
      for fname in extra:
         html_template = self.jinja_environment(fname, path=['templates', 'templates/extra'])
         filename = os.path.join('docs', fname)
         html = html_template.render(groups=self.database['groups'])
         self.write_file(filename, html)
      

   def html_index(self):
      print('\nRendering html index ...')

      # Main index
      html_template = self.jinja_environment('index-groups.html')
      filename = os.path.join('docs', 'index-groups.html')
      html = html_template.render(groups=self.database['groups'])
      self.write_file(filename, html)

      # Make html family index
      self.make_index('family')

      # Make html family_de index
      self.make_index('family_de')

      # Make html genus index
      self.make_index('genus', \
                      filter_func=lambda n:  n[0].upper() if len(n) else '')

      # Make html genus index
      self.make_index('genus_de', \
                      filter_func=lambda n:  n[0].upper() if len(n) else '')



   def make_index(self, index_name, filter_func=lambda n: n):
      sorted_species =  {}
      for specie in self.database['species']:
         for k in [index_name, 'genus', 'genus_de', 'specie', 'specie_de']:
            if not k in specie:
               specie[k] = '{unknown}'

         key = filter_func(specie[index_name])
         if key in sorted_species:
            sorted_species[key].append(specie)
         else:
            sorted_species[key] = [specie]
      keys = [k for k in sorted_species.keys()]
      keys.sort()
      self.index = {'keys': keys, 'species': sorted_species }
      self.index['index_name'] = index_name

      # Jinja template
      html_template = self.jinja_environment('index-de.html')
      html = html_template.render(index=self.index)
      output = os.path.join('docs', 'index-' + re.sub('[_ ]', '-', index_name)+'.html')
      self.write_file(output, html)


   def html_groups(self):
      print('\nRendering html groups ...')

      # Jinja environment
      html_template = self.jinja_environment('groups-de.html')

      # Make html group files
      for group_path, group in self.database['groups'].items():
         filename = os.path.join('docs', group['filename'] + '.html')
         html = html_template.render(group=group)
         self.write_file(filename, html)


   def html_species(self):
      print('\nRendering html species ...')

      # Jinja environment
      html_template = self.jinja_environment('species-de.html')

      # Make html files
      for register in self.database['species']:
         if not 'group' in register:
            continue
         filename = os.path.join('docs', register['filename'] + '.html')
         html = html_template.render(register=register)
         self.write_file(filename, html)


   def jinja_environment(self, template_file, path='templates'):
      # Setup Jinja environment
      jinja_env = Environment(
         loader=FileSystemLoader(searchpath=path, encoding='utf-8-sig') )
      return jinja_env.get_template(template_file)


   def write_file(self, filename, data):
      if self.overwrite or not os.path.isfile(filename):
         if self.verbose:
            print('   %s' % filename)
         with codecs.open(filename, 'w', encoding='utf-8') as fo:
            fo.write(data)
            return True
      return False


# --------------------------------------------------------------------
#    DATABASE CLASS
# --------------------------------------------------------------------

class Database(UserDict):

   def __init__(self):
      UserDict.__init__(self) 
      self['groups'] = {}
      self['species'] = []
      self.filenames = []


   def read(self, path):
      self.read_paths(path)
      self.test_errors()
      

   def read_paths(self, path):
      # Process files
      fnames = [f.lower() for f in os.listdir(path)]
      if 'index.txt' in fnames:
         self.read_data(path, 'index.txt')

      # Recurse subdirs
      for f in fnames:
         fullname = os.path.join(path, f)
         if os.path.isdir(fullname):
            self.read_paths(fullname)


   def read_data(self, path, fname):

      # Read yaml documents from file
      with codecs.open(os.path.join(path, fname), 'r', encoding='utf-8-sig') as fi:
         data = fi.read()
      docs = [d for d in yaml.load_all(data)]
        

      # Create register with first yaml document and add path
      self.register = docs[0]
      # Complete source path
      self.register['path'] = path.replace('\\', '/')
      # Path clasification
      self.register['splitpath'] = self.register['path'].split('/')[1:]

      if 'species' in self.register:
         # Register of species
         self.add_species(docs[1:])
      elif 'group_name' in self.register:
         # Register of group of species
         self.add_group()
      else:
         # Register unknown
         print('   Error, unknown type of register: %s' % fname)


   def add_species(self, sessions=None):
      # Generate species unique filename
      self.file_name()

      # Group path
      self.register['group_path'] = os.path.split(self.register['path'])[0]

      # Add photo sessions
      self.register['sessions'] = []
      if sessions:
         self.register['sessions'] = [s for s in sessions]

      # Store register in database
      self['species'].append(self.register)


   def add_group(self):
      # Generate group unique name
      self.file_name()

      # Add group species list
      self.register['species'] = []

      # Store register in database
      self['groups'][self.register['path']] = self.register


   def file_name(self):
      # Generate register name
      if 'genus' in self.register and 'species' in self.register:
         name = self.register['genus'] + '-' + self.register['species']
      else:
         name = '-'.join(self.register['splitpath'])

      # Normalize filename
      name = re.sub('[^a-zA-Z0-9]', '-', name).lower()
      name = re.sub('-+', '-', name)
      name = re.sub('-^', '', name).lower()

      # Test if duplicated
      if name in self.filenames:
         print('   Error, duplicated name: %s' % name)
      else:
         self.filenames.append(name)

      # Store filename
      self.register['filename'] = name


   def test_errors(self):
      print('\nFinding errors ...')

      # Test all species
      for register in self['species']:
         # Test if database images exists
         images = []
         for session in register['sessions']:
            for image in session['images']:
               if self.test_file(register['path'], image):
                  images.append(image)
         if 'thumb' in register and not register['thumb'] in images:
            if self.test_file(register['path'], register['thumb']):
               images.append(register['thumb'])
         else:
            register['thumb'] = images[0]

         # Test if image files are in database
         for file in os.listdir(register['path']):
            if file[-4:].lower() == '.jpg' and file not in images:
                  print('   Error, not in database: %s' % os.path.join(register['path'], file))

         # Link species with group
         group_path = register['group_path']
         if not group_path in self['groups']:
            print('   species without group: %s' % register['path'])
            continue
         group = self['groups'][group_path]
         if not register in group['species']:
             group['species'].append(register)
             register['group'] = group
         else:
            print('   duplicated species: %s' % group_path)

      # Delete empty groups
      clean_groups = {}
      for key, group in self['groups'].items():
         if group['species']:
            clean_groups[key] = group
      self['groups'] = clean_groups

      # Sort groups and link in chain
      keys = [k for k in self['groups'].keys()]
      keys.sort()
      for i in range(len(keys)-1):
         self['groups'][keys[i]]['group_next'] = self['groups'][keys[i+1]]
         self['groups'][keys[i]]['group_prev'] = self['groups'][keys[i-1]]
      self['groups'][keys[-1]]['group_next'] = self['groups'][keys[0]]
      self['groups'][keys[-1]]['group_prev'] = self['groups'][keys[-2]]

      # Sort species and link in chain
      all_species = []
      for key in keys:
         species = [s for s in self['groups'][key]['species']]
         species.sort(key=lambda s: s['filename'])
         all_species = all_species + species

      for i in range(len(all_species)-1):
         all_species[i]['species_next'] = all_species[i+1]
         all_species[i]['species_prev'] = all_species[i-1]
      all_species[-1]['species_next'] = all_species[0]
      all_species[-1]['species_prev'] = all_species[-2]


   # Test if file exists
   def test_file(self, path, file):
      filename = os.path.join(path, file)
      if not os.path.isfile(filename):
         print("   Error, file doesn't exitst: %s" % filename)
         return None
      return filename


# --------------------------------------------------------------------
#    READ OPTIONS, MAKE THUMBNAILS 
# --------------------------------------------------------------------

def read_options(fname):
   global options
   print('\nReading options ...')
   with codecs.open(os.path.join(fname), 'r', encoding='utf-8-sig') as fi:
      data = fi.read()
   options = yaml.load(data)
   

def make_thumbnails(database):
   print('\nMaking thumbnails ...')
   thumbfiles = {}
   for register in database['species']:
      for session in register['sessions']:
         for i, image in enumerate(session['images']):
            # Add relative path
            thumbname = image_name(register, image, session)
            if register['thumb'] == image:
               register['thumb'] = thumbname
            source_in = os.path.join(register['path'], image)
            image_out = os.path.join('docs', 'images', thumbname)
            thumb_out = os.path.join('docs', 'thumbs', thumbname)

            # Make thumbnail without overwrite
            if not os.path.isfile(thumb_out):
               thumbnail(source_in, thumb_out)

            # Copy image without overwrite
            if not os.path.isfile(image_out):
               shutil.copy2(source_in, image_out)


def thumbnail(filein, thumb):
   global options
   print('   Thumbnail: ' + thumb)
   options = ' '.join(options['thumb_options'])
   command = options['imagemagick'] + ' ' + filein + ' ' + options + ' ' + thumb
   subprocess.call(command, shell=True)


def image_name(register, imagename, session=None):
   thumbname = register['filename'] + '-' + re.sub('[^0-9]', '', imagename) + '.jpg'
   thumbname = re.sub('-+', '-', thumbname)
   if session:
      if not 'thumbs' in session:
         session['thumbs'] = []
      if thumbname in session['thumbs']:
         print('   Error, duplicated image: %s' % os.path.join(reg['path'], thumbname))
      else:
         session['thumbs'].append(thumbname)
   return thumbname


main()
