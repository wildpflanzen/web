"""

   Wildpflanzen static web generator.

   https://github.com/wildpflanzen/web


   Copyright (c) 2018-2021 by Carlos Pardo

   License GPL v3  <https://www.gnu.org/licenses/gpl-3.0.html>
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
   options = Options(file_name='options.ini')

   # Read database
   database = Database(options)
   database.read()

   # Make thumbnails
   thumbnails_make(database, options)

   # Make html pages
   generator = HTML_generator(database, options)

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
      self.database.options = options
      self.options = options
      
   def copy_static(self):
      print("\nCopying static files ...")
      self.copy_files('../templates', \
                      os.path.join(self.options.output, 'templates'))
      self.copy_files(os.path.join(self.options.source, 'static'), \
                      os.path.join(self.options.output, 'static'))
      self.copy_files('static', os.path.join(self.options.output, 'static'))
      self.copy_files('root', self.options.output)


   def copy_files(self, src, dst):
      if not os.path.isdir(dst):
         os.mkdir(dst)         
      for fname in os.listdir(src):
         if self.options.verbose:
            print('   %s' % fname)
         if os.path.isdir(os.path.join(src, fname)):
            if not os.path.exists(os.path.join(dst, fname)):
               os.mkdir(os.path.join(dst, fname))
            self.copy_files(os.path.join(src, fname), os.path.join(dst, fname))
         if os.path.isfile(os.path.join(src, fname)):
            if not os.path.exists(os.path.join(dst, fname)) or self.options.overwrite:
               shutil.copy2(os.path.join(src, fname), os.path.join(dst, fname))


   def html_extra(self):
      print('\nRendering html extra ...')
      path = 'extra'
      extra = [f for f in os.listdir(path) if f[-5:].lower() == '.html']
      for fname in extra:
         print('   ' + fname)
         html_template = self.jinja_environment(fname, path=['', 'extra'])
         filename = os.path.join(self.options.output, fname)
         html = html_template.render(database=self.database)
         self.write_file(filename, html)


   def html_index(self):
      print('\nRendering index files ...')

      # Make html besucher order index
      self.make_index('index-besucher-order', lambda sp: [sp['order']], index_type='Animalia')

      # Make html place index
      self.make_index('index-location', lambda sp: self.session_index(sp, 'location'))

      # Make html date index
      self.make_index('index-date', lambda sp: self.getdate(sp), length=8)

      # Make html genus index
      self.make_index('index-genus', lambda sp: [sp['genus']], length=1)

      # Make html genus_de index
      self.make_index('index-genus_de', lambda sp: self.deutchname(sp, 'genus_de', 'species_de'), sort_deutchname=True, length=1)

      # Make html family index
      self.make_index('index-family', lambda sp: [sp['family']])

      # Make html family_de index
      self.make_index('index-family_de', lambda sp: [sp['family_de']], sort_deutchname=True)


   def getdate(self, sp):
      result = []
      for d in self.session_index(sp, 'date'):
         fields = d.split('.')
         if len(fields) != 2:
            print('   Date error:', d, sp['genus'], sp['species'])            
            result.append(fields[0] + '.')
         else:
            result.append(fields[1] + '.%02d' % int(fields[0]))
      return result


   def make_index(self, index_name, fkey, template_name='index_species.html', length=0, sort_deutchname=False, index_type=False):
      sorted_species =  {}
      for species in self.database.species:
         index_species = False
         if index_type and 'makeindex' in species and species['makeindex'] == index_type:
            index_species = True
         if not index_type and not 'makeindex' in species:
            index_species = True
         if index_species == False:
            continue

         try:
            names = fkey(species)
         except:
            continue
         for name in names:
            # Test if name exists and select first character
            if not name:
               continue
            key = name if not length else name[:length]

            # Add new species
            if key in sorted_species:
               sorted_species[key].append(species)
            else:
               sorted_species[key] = [species]

      # Sort key characters
      keys = [k for k in sorted_species.keys()]
      keys.sort()

      # Sort species
      for key in keys:
         if sort_deutchname:
            sorted_species[key] = sorted(sorted_species[key], \
                                         key=lambda sp: self.deutchname(sp, 'genus_de', 'species_de'))
         else:
            sorted_species[key] = sorted(sorted_species[key], \
                                         key=lambda sp: sp['genus'] + sp['species'])
         

      # compose index
      self.index = {'keys': keys, 'species': sorted_species, 'index_name': index_name }

      # Jinja template
      html_template = self.jinja_environment(template_name)
      html = html_template.render(index=self.index, database=self.database)
      output = os.path.join(self.options.output, re.sub('[ _/]', '-', index_name)+'.html')
      self.write_file(output, html)


   def session_index(self, species, index):
      data = []
      if 'sessions' in species:
         for session in species['sessions']:
            if index in session:
               if session[index]:
                  data.append(session[index])
      if data :
         return data
      else:
         return ['']


   def deutchname(self, variable, index1, index2=''):
      # Extract deutsche names
      if index1 in variable and variable[index1]:
         if isinstance(variable[index1], list):
            res1 = variable[index1]
         else:
            res1 = [variable[index1]]
      if index2 and index2 in variable and variable[index2]:
         if isinstance(variable[index2], list):
            res2 = variable[index2]
         else:
            res2 = [variable[index2]]
      # combine names
      res = []
      for i in range(len(res1)):
         name = res1[i] + ' ' + res2[i]
         res.append(name.strip(' '))
      return res


   def html_groups(self):
      print('\nRendering html groups ...')

      # Make html group files
      for group in self.database.groups:

         # Select Jinja environment
         if 'group_template' in group:
            html_template = self.jinja_environment(group['group_template'])
         else:
            html_template = self.jinja_environment('groups.html')

         # Render template
         filename = os.path.join(self.options.output, group['filename'] + '.html')
         html = html_template.render(group=group, database=self.database)
         self.write_file(filename, html)


   def html_species(self):
      print('\nRendering html species ...')

      # Jinja environment
      html_template = self.jinja_environment('species.html')

      # Make html files
      for species in self.database.species:
         if not 'group' in species:
            continue
         filename = os.path.join(self.options.output, species['filename'] + '.html')
         html = html_template.render(species=species, database=self.database)
         self.write_file(filename, html)


   def jinja_environment(self, template_file, path=''):
      # Setup Jinja environment
      jinja_env = Environment(
         loader=FileSystemLoader(searchpath=path, encoding='utf-8-sig') )
      return jinja_env.get_template(template_file)


   def write_file(self, filename, data):
      if os.path.exists(filename):
         with codecs.open(filename, 'r', encoding='utf-8') as fi:
            data_in_disk = fi.read()
         if data == data_in_disk:
            return False
      if self.options.verbose:
         print('   %s' % filename)
      with codecs.open(filename, 'w', encoding='utf-8') as fo:
         fo.write(data)
      return True


# --------------------------------------------------------------------
#    DATABASE
# --------------------------------------------------------------------

class Database(UserDict):

   def __init__(self, options):
      UserDict.__init__(self)
      self.groups = []
      self.species = []
      self.filenames = []
      self.options = options


   def read(self):
      print('\nReading database ...')
      self.read_paths(self.options.source)
      self.test_errors()
      self.combine_database()


   def read_paths(self, basepath, path='', parent=None):
      # Process files
      group = None
      fnames = os.listdir(os.path.join(basepath, path))
      fnames.sort()
      for fname in fnames:
         if 'index.txt' in fname.lower():
            group = self.read_data(basepath, path, fname, parent)

      # Recurse subdirs
      subdirs = []
      if group and 'listdir' in group:
         for diname in group['listdir']:
            subdirs.append(diname)
            fullname = os.path.join(basepath, path, diname)
            if not os.path.exists(fullname) or not os.path.isdir(fullname):
               print("   Error, path %s doesn't exists: %s" % (diname, os.path.join(path, 'index.txt')))
               continue
            self.read_paths(basepath, path=os.path.join(path, diname), parent=group)

      for diname in fnames:
         if diname == 'static' and path=='':
            continue
         if diname in subdirs:
            continue
         fullname = os.path.join(basepath, path, diname)
         if os.path.isdir(fullname):
            #print("   Warning, path %s not in listdir: %s" % (diname, os.path.join(path, 'index.txt')))
            self.read_paths(basepath, path=os.path.join(path, diname), parent=group)


   def read_data(self, basepath, path, fname, parent):

      # Read yaml documents from file
      fullpath = os.path.join(basepath, path)
      with codecs.open(os.path.join(fullpath, fname), 'r', encoding='utf-8-sig') as fi:
         data = fi.read()
      try:
         docs = [d for d in yaml.load_all(data, Loader=yaml.Loader)]
      except:
         raise Exception('Error reading: ' + os.path.join(fullpath, fname)) 

      # Create register with first yaml document and add path
      register = docs[0]
      # Complete source path
      register['path'] = path.replace('\\', '/')
      # Path clasification
      register['splitpath'] = register['path'].split('/')

      if 'species' in register:
         # Register species
         self.add_species(register, docs[1:])
      elif 'group_title' in register or 'listdir' in register:
         # Register group of species
         self.add_group(register, parent)
         return register
      else:
         # Register unknown
         print('   Error, unknown type of register: %s' % os.path.join(register['path'], fname))
      return None


   def add_species(self, register, sessions=None):
      # Generate species unique filename
      self.file_name(register)

      # Group path
      register['group_path'] = os.path.split(register['path'])[0]

      # Add photo sessions
      register['sessions'] = []
      if sessions:
         register['sessions'] = [s for s in sessions]

      # Store register in database
      self.species.append(register)


   def add_group(self, register, parent):
      # Generate group unique name
      self.file_name(register)

      # Add parent group
      register['parent'] = parent

      # Add group species list
      register['species'] = []

      # Store register in database
      self.groups.append(register)


   def file_name(self, register):
      # Generate register name
      if 'genus' in register and 'species' in register:
         name = register['genus'] + '-' + register['species']
      else:
         name = '-'.join(register['splitpath'])

      # Normalize filename
      name = re.sub('[^a-zA-Z0-9]', '-', name).lower()
      name = re.sub('-+', '-', name)
      name = re.sub('-^', '', name).lower()

      # Test if duplicated
      if name in self.filenames:
         print('   Error, duplicated name: %s' % os.path.join(register['path'], name))
      else:
         self.filenames.append(name)

      # Store filename
      register['filename'] = name


   def test_errors(self):
      print('\nFinding errors ...')

      # Test all species
      for register in self.species:

         # Test if database images exists
         images = []
         for session in register['sessions']:
            for image in session['images']:
               if self.test_file(register['path'], image):
                  images.append(image)

         # Test thumbnail image
         if 'thumb' in register and register['thumb']:
            if not register['thumb'] in images:
               print('   Error, thumbnail not in image list: %' % os.path.join(register['path'], register['thumb']))
            if self.test_file(register['path'], register['thumb']):
               if not register['thumb'] in images:
                  images.append(register['thumb'])
            else:
               register['thumb'] = images[0] if len(images) else ''

         # Test if source image files are in database
         for file in os.listdir(os.path.join(self.options.source, register['path'])):
            if file[-4:].lower() == '.jpg' and file not in images:
               print('   Warning, image file not in database: %s' % os.path.join(register['path'], file))

         # Create empty keys
         for key in ['family', 'genus', 'species',
                     'family_de', 'genus_de', 'species_de']:
            if not key in register:
               register[key] = ''

         # Change string to list of strings in genus_de and species_de
         if not isinstance(register['genus_de'], list):
            register['genus_de'] = [ register['genus_de'] ]
         if not isinstance(register['species_de'], list):
            register['species_de'] = [ register['species_de'] ]
         if len(register['species_de']) != len(register['genus_de']):
            print('   Error, different number of deutsche names: %s' % os.path.join(register['path'], 'index.txt'))

         # Test deutsche name
         if register['splitpath'][1] in ['blumen']:
            for i in range(len(register['species_de'])):
               if register['genus_de'][i] and len(register['species_de'][i])<1:
                  print('   Warning, deutsche genus without specie: %s' % os.path.join(register['path'], 'index.txt'))
               elif ' ' in register['species_de'][i] and register['species_de'][i][-1] != '-':
                  print('   Warning, subspecie without hyphen: %s' % os.path.join(register['path'], 'index.txt'))

         # Test Uppercase and lowercase
         if register['family'] and not re.match(u'[A-Z]', register['family']):
            print('   Warning, family first letter not Uppercase: %s' % os.path.join(register['path'], 'index.txt'))
         if register['species'] and not re.match(u'[a-z1-9]', register['species']):
            print('   Warning, species first letter not lowercase: "%s", %s' % (register['species'], os.path.join(register['path'], 'index.txt')))
         if register['genus'] and not re.match(u'[A-Z]', register['genus']):
            print('   Warning, genus first letter not Uppercase: %s' % os.path.join(register['path'], 'index.txt'))
         if register['family_de'] and not re.match(u'[A-ZÄËÏÖÜ]', register['family_de']):
            print('   Warning, family_de first letter not Uppercase: %s' % register['family_de'], os.path.join(register['path'], 'index.txt'))
         for i in range(len(register['species_de'])):
            if register['species_de'][i] and not re.match(u'[A-ZÄËÏÖÜ]', register['species_de'][i]):
               print('   Warning, species_de first letter not Uppercase: %s' % os.path.join(register['path'], 'index.txt'))
         for i in range(len(register['genus_de'])):
            if register['genus_de'][i] and not re.match(u'[A-ZÄËÏÖÜ]', register['genus_de'][i]):
               print('   Warning, genus_de first letter not Uppercase: %s' % os.path.join(register['path'], 'index.txt'))            
         if 'sessions' in register:
            for session in register['sessions']:
               if 'location' in session and session['location'] and not re.match(u'[A-ZÄËÏÖÜ]', session['location']):
                  print('   Warning, location first letter not Uppercase: %s' % os.path.join(register['path'], 'index.txt'))

         # Test date
         if 'sessions' in register:
            for session in register['sessions']:
               if 'date' in session and session['date'] and not re.match('(?:1[0-2]|[0-9])\.20[1-3][0-9]$', session['date']):
                  print('   Warning, date with bad format: %s, %s' % (session['date'], os.path.join(register['path'], 'index.txt')))

         # Link species with group
         group_path = register['group_path']
         group = self.find_group(group_path)
         if group:
            group = self.find_group(group_path)
            if not register in group['species']:
               group['species'].append(register)
               register['group'] = group
            else:
               print('   Error, duplicated species: %s' % group_path)
         else:
            print('   Warning, species without group: %s' % register['path'])

      # Delete empty groups
      used_groups = []
      for group in self.groups:
         if group['species']:
            used_groups.append(group)
      self.groups = used_groups


   def find_group(self, group_path):
      """Find group by path"""
      for group in self.groups:
         if group['path'] == group_path:
            return group
      return None


   def combine_database(self):
      # Link groups in chain
      for i in range(len(self.groups)-1):
         self.groups[i]['group_next'] = self.groups[i+1]
         self.groups[i]['group_prev'] = self.groups[i-1]
      self.groups[-1]['group_next'] = self.groups[0]
      if len(self.groups) > 1:
          self.groups[-1]['group_prev'] = self.groups[-2]
      else:
          self.groups[-1]['group_prev'] = self.groups[0]

      # Link Species in chain
      all_species = []
      for group in self.groups:
         all_species = all_species + group['species']

      for i in range(len(all_species)-1):
         all_species[i]['species_next'] = all_species[i+1]
         all_species[i]['species_prev'] = all_species[i-1]
      all_species[-1]['species_next'] = all_species[0]
      if len(all_species) > 1:
         all_species[-1]['species_prev'] = all_species[-2]
      else:
         all_species[-1]['species_prev'] = all_species[0]

      # Make manual links, from field next_group
      for group in self.groups:
         if 'next_group' in group:
            next_group = self.find_group(group['next_group'])
            if next_group:
               # relink next group
               group['group_next'] = next_group
               next_group['group_prev'] = group
               # relink next species of last species in group
               group['species'][-1]['species_next'] = next_group['species'][0]
               next_group['species'][0]['species_prev'] = group['species'][-1]
            else:
               print('   Warning, next path group does not exists: %s' % group['next_group'])


   # Test if file exists
   def test_file(self, path, file):
      filename = os.path.join(self.options.source, path, file)
      if self.options.ignore_images:
         return filename
      if os.path.isfile(filename):
         return filename
      print("   Error, file doesn't exitst: %s" % filename)
      return None


# --------------------------------------------------------------------
#    READ OPTIONS
# --------------------------------------------------------------------

class Options():

   def __init__(self, file_name=''):
      if file_name:
         options_dict = self.read(file_name)
         self.set_options(options_dict)
   
   def read(self, file_name):
      print('\nReading options ...')
      with codecs.open(file_name, 'r', encoding='utf-8-sig') as fi:
         options_raw = fi.read()
      options_dict = yaml.load(options_raw, Loader=yaml.Loader)
      return options_dict
   
   def set_options(self, options_dict):
      for key, val in options_dict.items():
         setattr(self, key, val)

   def __repr__(self):
      return yaml.dump(self.__dict__)

   def __getitem__(self, key):
      if key in self.__dict__:
         return self.__dict__[key]
      if not key in self.__dict__:
         return False
   

# --------------------------------------------------------------------
#    MAKE THUMBNAILS
# --------------------------------------------------------------------

def makedir(path):
   if not os.path.exists(path):
      os.mkdir(path)


def thumbnails_make(database, options):
   if options.ignore_images:
      return
   print('\nMaking thumbnails ...')

   all_image_files = []

   for register in database.species:
      thumbname = ''
      for session in register['sessions']:
         if not 'thumbs' in session:
            session['thumbs'] = []

         for i, image in enumerate(session['images']):

            # Make imagename and test if duplicated
            imagename = image_name(register, image)
            if imagename in all_image_files:
               print('   Error, duplicated image: %s' % os.path.join(register['path'], imagename))
               continue
            all_image_files.append(imagename)

            # Add relative path to images
            source_in = os.path.join(options.source, register['path'], image)
            image_out = os.path.join(options.output, 'images', imagename)
            thumb_out = os.path.join(options.output, 'thumbs', imagename)

            # Copy image if source is newer
            if not (os.path.isfile(image_out) and file_newer(image_out, source_in)):
               if options.verbose:
                  print('   Copy %s -->\n        %s' %(source_in, image_out))
               image_convert(source_in, image_out, options)

            # Select main thumbnail
            if not thumbname:
               thumbname = imagename
            if 'thumb' in register and register['thumb'] == image:
               thumbname = imagename

            # Store thumbnails names
            session['thumbs'].append(imagename)

            # Make thumbnail without overwrite
            if not (os.path.isfile(thumb_out) and file_newer(thumb_out, source_in)):
               thumb_convert(source_in, thumb_out, options)

         register['thumbname'] = thumbname

   # Search for unused image files
   remove_unused_files('images', all_image_files, options)
   remove_unused_files('thumbs', all_image_files, options)


def remove_unused_files(path, used_image_files, options):
   fullpath = os.path.join(options.output, path)
   for image in os.listdir(fullpath):
      if not image in used_image_files:
         print('   Warning, unused image: %s' % os.path.join(fullpath, image))
         if options.remove_unused_files:
            os.remove(os.path.join(fullpath, image))


def image_convert(image_in, image_out, options):
   print('   Image: ' + image_in)
   image_options = ' '.join(options.image_options)
   command = options.imagemagick + ' ' + image_in + ' ' + image_options + ' ' + image_out
   subprocess.call(command, shell=True)


def file_newer(filename_1, filename_2):
   if os.path.getmtime(filename_1) > os.path.getmtime(filename_2):
      return True
   return False


def thumb_convert(filein, thumb, options):
   print('   Thumbnail: ' + thumb)
   thumb_options = ' '.join(options.thumb_options)
   command = options.imagemagick + ' ' + filein + ' ' + thumb_options + ' ' + thumb
   subprocess.call(command, shell=True)


def image_name(register, imagename):
   thumbname = register['filename'] + '-' + re.sub('[^0-9]', '', imagename) + '.jpg'
   thumbname = re.sub('-+', '-', thumbname)
   return thumbname


# --------------------------------------------------------------------
#    CALL MAIN FUNCTION
# --------------------------------------------------------------------

main()
