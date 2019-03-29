# -*- coding: utf-8 -*-
"""
   Read all html files of a directory and subdirectories, and
   write out a sitemap.xml file of all.
   
   ----------------------------------------------------------------
   
   :copyright: (c) 2018 by Carlos Pardo <carlos (at) picuino.com>
   :license: GPL v3  <https://www.gnu.org/licenses/gpl-3.0.html>
   
   This program is free software; you can redistribute it and/or
   modify it under the terms of the GNU General Public License
   version 3 as published by the Free Software Foundation.

"""

import os
import re
import time
import codecs
import sys
from jinja2 import Environment, FileSystemLoader, Template

data = {
   'site': "http://www.wildpflanzen.com.de/",
}


sitemap_template = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{% for f in data.files %}
<url>
  <loc>{{data.site}}{{f.name}}</loc>
  <lastmod>{{f.timestamp}}</lastmod>
  <changefreq>weekly</changefreq>
  <priority>1.00</priority>
</url>
{%- endfor %}

</urlset>
"""


def main():
   # Read arguments
   pathname = '../docs'
   output = os.path.join(pathname, 'sitemap.xml')
   if not os.path.isdir(pathname):
      print("Argument pathname doesn't exists")
      return
	  
   # Read all files
   print('   Sitemap of: %s' % (pathname))
   data['files'] = html_files(pathname)

   # Render files and write output
   code = Template(sitemap_template).render(data=data)

   with codecs.open(output, 'w', encoding='utf-8') as fo:
      fo.write(code)


def html_files(path):
   files = []
   dirs = []
   for f in os.listdir(path):
      longname = os.path.join(path, f)
      if os.path.isfile(longname):
         base, ext = os.path.splitext(f)
         if ext.lower() in ['.html', '.htm']:
            timestamp = time.strftime("%Y-%m-%d", time.gmtime(os.path.getmtime(longname)))
            files.append({'name':f, 'timestamp':timestamp})
   return files
         
main()
