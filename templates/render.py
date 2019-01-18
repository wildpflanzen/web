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

def main():

   # Read options
   options = read_options('options.ini')

   # Read database
   print('\nReading data ...')
   database = Database(options)
   database.read()

   # Make thumbnails
   make_thumbnails(database, options)

   # Make html pages
   generator = HTML_generator(database, options)
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

   def __init__(self, database, options):
      self.database = database
      self.overwrite = False
      self.verbose = options['verbose']
      self.output = options['output']
      self.source = options['source']
      

   def copy_static(self):
      print("\nCopying static files ...")
      self.copy_files(self.source + '/static', self.output + '/static')
      self.copy_files('root', self.output)
      self.copy_files('static', self.output + '/static')     


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
      path = 'extra'
      extra = [f for f in os.listdir(path) if f[-5:].lower() == '.html']
      for fname in extra:
         html_template = self.jinja_environment(fname, path=['', 'extra'])
         filename = os.path.join(self.output, fname)
         html = html_template.render(groups=self.database['groups'])
         self.write_file(filename, html)
      

   def html_index(self):

      # Make html genus index
      self.make_index('genus')

      # Make html genus_de index
      for specie in self.database['species']:
         specie['name_de'] = self.getindex(specie, 'genus_de', 'species_de')
      self.make_index('genus_de', 'species_de')

      # Make html family index
      self.make_index('family')

      # Make html family_de index
      self.make_index('family_de')


   def getindex(self, variable, index1, index2=''):
      res = ''
      if index1 in variable and variable[index1]:
         if isinstance(variable[index1], list):
            res = variable[index1][0]
         else:
            res = variable[index1]
      if index2 and index2 in variable and variable[index2]:
         if isinstance(variable[index2], list):
            res = res + ' ' + variable[index2][0]
         else:
            res = res + ' ' + variable[index2]
      res = res.strip(' ')
      return res

                
   def make_index(self, index1, index2=''):
      print('\nRendering index: %s %s' % (index1, index2)) 
      sorted_species =  {}
      for specie in self.database['species']:
         name = self.getindex(specie, index1, index2)

         # Test if name exists and select first character
         if not name:
            if self.verbose: print('x', sep='', end='')
            continue
         else:
            if self.verbose: print('.', sep='', end='')
         key = name[0].upper()

         # Add new specie
         if key in sorted_species:
            sorted_species[key].append(specie)
         else:
            sorted_species[key] = [specie]
      if self.verbose: print()

      # Sort key characters
      keys = [k for k in sorted_species.keys()]
      keys.sort()
      self.index = {'keys': keys, 'species': sorted_species }
      self.index['index_name'] = index1

      # Jinja template
      html_template = self.jinja_environment('index-de.html')
      html = html_template.render(index=self.index)
      output = os.path.join(self.output, 'index-' + re.sub('[_ ]', '-', index1)+'.html')
      self.write_file(output, html)

 
   def html_groups(self):
      print('\nRendering html groups ...')

      # Jinja environment
      html_template = self.jinja_environment('groups-de.html')

      # Make html group files
      for group_path, group in self.database['groups'].items():
         filename = os.path.join(self.output, group['filename'] + '.html')
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
         filename = os.path.join(self.output, register['filename'] + '.html')
         html = html_template.render(species=register)
         self.write_file(filename, html)


   def jinja_environment(self, template_file, path=''):
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

   def __init__(self, options):
      UserDict.__init__(self) 
      self['groups'] = {}
      self['species'] = []
      self.filenames = []
      self.source = options['source']


   def read(self):
      self.read_paths(self.source)
      self.test_errors()
      self.combine_database()
      

   def read_paths(self, basepath, path=''):
      # Process files
      fnames = os.listdir(os.path.join(basepath, path))
      for f in fnames:
         if 'index.txt' in f.lower():
            self.read_data(basepath, path, f)

      # Recurse subdirs
      for f in fnames:
         fullname = os.path.join(basepath, path, f)
         if os.path.isdir(fullname):
            self.read_paths(basepath, os.path.join(path, f))


   def read_data(self, basepath, path, fname):

      # Read yaml documents from file
      fullpath = os.path.join(basepath, path)
      with codecs.open(os.path.join(fullpath, fname), 'r', encoding='utf-8-sig') as fi:
         data = fi.read()
      docs = [d for d in yaml.load_all(data)]
        

      # Create register with first yaml document and add path
      self.register = docs[0]
      # Complete source path
      self.register['path'] = path.replace('\\', '/')      
      # Path clasification
      self.register['splitpath'] = self.register['path'].split('/')

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
         print(self.register)
         input()
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
                  
         # Test thumbnail image
         if 'thumb' in register and not register['thumb'] in images:
            if self.test_file(register['path'], register['thumb']):
               images.append(register['thumb'])
         else:
            register['thumb'] = images[0]

         # Test if image files are in database
         for file in os.listdir(os.path.join(self.source, register['path'])):
            if file[-4:].lower() == '.jpg' and file not in images:
               print('   Error, not in database: %s' % os.path.join(register['path'], file))
               
         # Create empty keys
         for key in ['family', 'genus', 'species',
                     'family_de', 'genus_de', 'species_de']:
            if not key in register:
               register[key] = ''

         # Force list in deutche genus and species
         if not isinstance(register['genus_de'], list):
            register['genus_de'] = [ register['genus_de'] ]
         if not isinstance(register['species_de'], list):
            register['species_de'] = [ register['species_de'] ]
         if len(register['species_de']) != len(register['genus_de']):
            print('   Error, different number of deutche names: %s' % os.path.join(register['path'], 'index.txt'))

         # Test deutche name
         if register['splitpath'][1] in ['blumen']:
            for i in range(len(register['species_de'])):
               if register['genus_de'][i] and len(register['species_de'][i])<1:
                  print('   Warning, deutche genus without specie: %s' % os.path.join(register['path'], 'index.txt'))
               elif ' ' in register['species_de'][i] and register['species_de'][i][-1] != '-':
                  print('   Warning, subspecie without hyphen: %s' % os.path.join(register['path'], 'index.txt'))
         
         # Link species with group
         group_path = register['group_path']
         if not group_path in self['groups']:
            print('   Warning, species without group: %s' % register['path'])
            continue
         group = self['groups'][group_path]
         if not register in group['species']:
             group['species'].append(register)
             register['group'] = group
         else:
            print('   Error, duplicated species: %s' % group_path)

      # Delete empty groups
      used_groups = {}
      for key, group in self['groups'].items():
         if group['species']:
            used_groups[key] = group
      self['groups'] = used_groups


   def combine_database(self):
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
      filename = os.path.join(self.source, path, file)
      if not os.path.isfile(filename):
         print("   Error, file doesn't exitst: %s" % filename)
         return None
      return filename


# --------------------------------------------------------------------
#    READ OPTIONS, MAKE THUMBNAILS 
# --------------------------------------------------------------------

def read_options(fname):   
   print('\nReading options ...')
   with codecs.open(os.path.join(fname), 'r', encoding='utf-8-sig') as fi:
      data = fi.read()
   options = yaml.load(data)
   return options
   

def make_thumbnails(database, options):
   print('\nMaking thumbnails ...')
   thumbfiles = {}
   for register in database['species']:
      for session in register['sessions']:
         for i, image in enumerate(session['images']):
            # Add relative path
            thumbname = image_name(register, image, session)
            register['thumbname'] = thumbname
            source_in = os.path.join(register['path'], image)
            image_out = os.path.join(options['output'], 'images', thumbname)
            thumb_out = os.path.join(options['output'], 'thumbs', thumbname)

            # Make thumbnail without overwrite
            if not os.path.isfile(thumb_out):
               thumbnail(source_in, thumb_out, options)

            # Copy image without overwrite
            if not os.path.isfile(image_out):
               shutil.copy2(source_in, image_out)


def thumbnail(filein, thumb, options):
   print('   Thumbnail: ' + thumb)
   thumb_options = ' '.join(options['thumb_options'])
   command = options['imagemagick'] + ' ' + filein + ' ' + thumb_options + ' ' + thumb
   subprocess.call(command, shell=True)


def image_name(register, imagename, session=None):
   global options
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
