"""
   Wildpflanzen static web site generator

   LICENSE
   =======
   This source code was written by Picuino <picuino@gmail.com>,
   and is published under the following license:

   Permission is hereby granted, free of charge, to any person obtaining a copy
   of this software and associated documentation files (the "Software"), to deal
   in the Software without restriction, including without limitation the rights
   to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
   copies of the Software, and to permit persons to whom the Software is
   furnished to do so, subject to the following conditions:
 
   The above copyright notice and this permission notice shall be included in
   all copies or substantial portions of the Software.

   THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
   IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
   FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
   AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
   LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
   FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
   IN THE SOFTWARE.
   
"""
import pyratemp
import codecs
import os
import re
import time
from database import *
import html

BlumenColors = [
   "blau",
   "gelb",
   "gruen_braun",
   "rot",
   "weiss",
   "gruen"
]

BlumeFields = [
   "color", "type",
   "specie", "family",
   "name_de", "name_index_de", "family_de", "comment_de","comment_de_zeit",
   "name_es", "family_es", "comment_es",
   "date", "location",
   "thumb", "images",
]

ImageFields = [
   "src",
   "comment_de", "comment_es",
]

update_data = True

overwrite_html = False  # No cambiar. El valor cambia al responder la pregunta que aparece al comienzo del programa

#=====================================================================
#   Main Program
#=====================================================================
def main():

   # ask if overwrite html
   global overwrite_html
   if ask("\n\n\nDo you want to overwrite html pages? (y/N):", "[ysj]"):
      print "Overwriting pages"
      overwrite_html = True
   else:
      overwrite_html = False
   

   # Parse all html pages
   path = ".."
   allblumen = DataBase()
   for BlumenColor in BlumenColors:
      alltypes = parse_blumencolor(path, BlumenColor)
      allblumen.append(alltypes)

   # Write html index page for all blumen
   print "Parsing index files:"
   make_index(path, allblumen, "specie", 1, "Template_index_de.html", "register_de_w.html")
   make_index(path, allblumen, "name_index_de", 1, "Template_index_de.html", "register_de.html")
   make_index(path, allblumen, "family", 99, "Template_index_de.html", "register_family_de_w.html")
   make_index(path, allblumen, "family_de", 99, "Template_index_de.html", "register_family_de.html")
   make_alldata(path, allblumen, "Template_all_data.html", "alldata.html")

   print "Total blumen =", len(allblumen)


#=====================================================================

def ask(question, condition):
   """Ask for a question. Return True if condition in answer"""
   ans = raw_input(question)
   if re.search(condition, ans.lower()):
      return True
   return False


#=====================================================================

def parse_blumencolor(path, BlumenColor):
   """Write all html of a blumen color"""
   BlumenTypes = listdir(os.path.join(path, BlumenColor))

   allcolors = DataBase()
   for BlumenType in BlumenTypes:
      blumen = parse_blumentype(path, BlumenColor, BlumenType)
      allcolors.append(blumen)

   return allcolors


#=====================================================================

def parse_blumentype(path, BlumenColor, BlumenType):
   """Write all html of a blumen type"""
   basename = os.path.join(path, BlumenColor, BlumenType)
   
   print "Parsing path:", basename
   dirnames = listdir(basename)
   
   allblumen = DataBase()
   for BlumeDir in dirnames:
      blume = make_blume(path, BlumenColor, BlumenType, BlumeDir)
      allblumen.append(blume)

   make_type(allblumen, basename, BlumenColor, BlumenType)
     
   return allblumen


#=====================================================================

def make_blume(path, BlumeColor, BlumeType, BlumeDir):
   print "  Parsing blume:", BlumeDir

   blume = load_data(path, BlumeColor, BlumeType, BlumeDir)
   
   if blume:
      blume.dirname = BlumeDir
      basename = os.path.join(path, BlumeColor, BlumeType)
      template_write(blume, "Template_blume_de.html",
                     os.path.join(basename, BlumeDir + "_de.html"))
   return blume


#=====================================================================

def make_type(allblumen, path, BlumenColor, BlumenType):
   """Write html index page for blumen type"""

   if not allblumen:
      print "  Type without blumen"
      return
   
   pagename = BlumenColor + BlumenType
   print "  Parsing index:", pagename

   # Make index of all blumen
   blumen_index = [blume.dirname for blume in allblumen] 
   data_index = load_index(os.path.join(path, "index.txt"))      
   changes = compare_list(data_index, blumen_index)
   if changes:
      open(os.path.join(path, "index.txt"), "w").write("\n".join(data_index))

   # Split pages
   subtypes = [[]]
   for index in data_index:
      if '---' in index[:3]:
         subtypes.append([])
      else:
         subtypes[-1].append(index)
   subtypes = [subtype for subtype in subtypes if len(subtype)>0]

   # make pages         
   numpages = len(subtypes)
   for i, blumen_index in enumerate(subtypes):
      blumen_sorted = database_extract(allblumen, blumen_index)
      blumen_sorted.numpages = numpages
      blumen_sorted.currentpage = i+1
      blumen_sorted.pagename = pagename
  
      # Write html index
      filename = "%s_de_%d.html" % (pagename, i+1)
      template_write(blumen_sorted, "Template_type_de.html",
                  os.path.join(path, filename))
         
   print "  Blumen in path = %d" % len(allblumen)


#=====================================================================         

def compare_list(list1, list2):
   """Add new elements of list2 to list1
      delete in list1 elements not in list2
      Return True if list1 change"""
   changes = False
   for element in list2:
      if not element in list1:
         list1.append(element)
         changes = True
   for element in list1:
      if not element in list2:
         if element[:3] == "---":
            continue
         list1.remove(element)
         changes = True
   return changes


#=====================================================================

def database_extract(database, sortlist):
   """Extract and return an ordered list of records of database
      according sortlist"""
   extract = DataBase()
   database = [record for record in database]
   
   for index in sortlist:
      for record in database:
         if index == record.dirname:
            extract.append(record)
            break
      
   return extract


#=====================================================================

def make_index(path, allblumen, indexname, indexlen, templatename, filename):
   """Write index for all blumen"""
   print "  Parsing index:", filename

   # Group blumen with indexname
   allblumen.sort(indexname, "specie")
   alfa_blumen = Record()
   alfa_blumen.indexname = indexname
   for blume in allblumen:
      if not blume[indexname]:
         index = "-"
      else:
         index = blume[indexname][:indexlen]
      if index in alfa_blumen:
         alfa_blumen[index].append(blume)
      else:
         alfa_blumen[index] = [blume]

   for index in alfa_blumen:
      alfa_blumen[index] = sorted(alfa_blumen[index])
      
   # Write html index page for all blumen
   template_write(alfa_blumen, templatename,
                  os.path.join(path, filename))


#=====================================================================

def make_alldata(path, allblumen, templatename, filename):
   """ Write html with all blumen data"""
   print "  Parsing index: alldata.html"
   allblumen.sort("type", "color", "specie")
   template_write(allblumen, templatename,
                  os.path.join(path, filename))


#=====================================================================

def listdir(path):
   """Return the list of directories in path"""
   try:
      filenames = os.listdir(path)
      filenames = [dirname for dirname in filenames if
                   os.path.isdir(os.path.join(path, dirname))]   
   except:
      filenames = []
   return filenames

#=====================================================================

def template_write(data, templatename, filename):
   """Write html template with data"""
   if os.path.exists(filename) and overwrite_html==False:
      return
   print "    Writing html..."
   pyte = pyratemp.Template(filename=templatename)
   page = pyte(data=data)
   page = html.encode(page)
   # Delete BOM 
   if type(page) == unicode:
      if page[0] == u'\ufeff' or page[0] == u'\ufffe':
         page = page[1:]
   # write file
   fout = codecs.open(filename, encoding='ascii', mode="w")
   fout.write(page.encode("ascii", "xmlcharrefreplace"))
   fout.close()
   

#=====================================================================

def load_index(filename, min_len=3):
   """Read file with list of blumen sorted"""
   if not os.path.exists(filename):
      return []
   index = open(filename, "r").read().split("\n")
   index = [row.strip() for row in index]
   index = [row for row in index if len(row)>=min_len]
   return index


#=====================================================================

def load_data(path, BlumeColor, BlumeType, BlumeDir):
   """Read data of blumen"""
   basename = os.path.join(path, BlumeColor, BlumeType, BlumeDir)
   if not os.path.isfile(os.path.join(basename, "Data.txt")) or update_data:
      print "    Extracting and writing Data.txt"
      # Read old data
      blume = extract_data(path, BlumeColor, BlumeType, BlumeDir, "Data.txt")
      if blume["images"]:
         blume.write(os.path.join(basename, "Data.txt"))
      else:
         return Record()

   blume = Record(os.path.join(basename, "Data.txt"), BlumeFields)

   fill_data(blume, BlumeColor, BlumeType)

   return blume


#=====================================================================

def fill_data(blume, BlumeColor, BlumeType):
   # Add name_index_de if don't exists
   deutch_name(blume)

   # Add family if don't exists
   if len(blume["family"])==0:
      if blume["specie"]:
         blume["family"] = blume["specie"].split(" ")[0]

   # Set color and type
   if not blume["color"]:
      blume["color"] = BlumeColor
   if not blume["type"]:
      blume["type"] = BlumeType


#=====================================================================

def deutch_name(blume):
   if len(blume["name_de"])>0 and not blume["name_index_de"]:
      names = blume["name_de"].split(" ")
      if len(names) == 1:
         blume["name_index_de"] = blume["name_de"]
      else:
         blume["name_index_de"] = " ".join(names[1:]) + ", " + names[0]

   if len(blume["name_de"])==0 and len(blume["name_index_de"])>0:
      names = blume["name_de"].split(", ")
      if len(names) != 2:
         blume["name_de"] = blume["name_index_de"]
      else:
         blume["name_de"] = names[-1] + " " + names[0]


#=====================================================================

def extract_data(path, BlumeColor, BlumeType, BlumeDir, filename):
   """Read data from data.txt, old html pages and files in directory"""
   basename = os.path.join(path, BlumeColor, BlumeType, BlumeDir)

   # Read data.txt
   if os.path.exists(os.path.join(basename, filename)):
      data = open(os.path.join(basename, filename), "r").read()
      if re.search("blumen =", data[:10]):
         exec(data)
         blume = Record(blumen, BlumeFields)
         blume["images"] = [Record({"src": i[0]}, ImageFields) for i in images]
         del blume["comment"]
      else:
         blume = Record(os.path.join(basename, filename), BlumeFields)
   else:
      blume = Record(fields=BlumeFields)
      
   # Read directory files
   thumb_filter = "_k\.|^0\.|thumb|-w[0-9][0-9][0-9]"
   files = [name for name in os.listdir(basename) if name[-3:].lower() == "jpg"]
   thumbs = [name for name in files if re.search(thumb_filter, name.lower())]
   imagefiles = [name for name in files if not re.search(thumb_filter, name.lower())]
   htmls = [name for name in os.listdir(basename) if re.search(".htm", name[-5:].lower())]
   
   if not imagefiles:
      print "    Blume without images"

   # Write blume data
   if not blume["specie"]:
      specie = re.sub("[_-]", " ", BlumeDir).title()
      blume["specie"] = specie

   # read deutch name from old html
   if htmls and not blume["name_de"]:
      fi = open(os.path.join(basename, htmls[0]), "rt")
      for line in fi:
         if re.search("<h4>", line) and re.search("<i>", line):
            line = re.split('/(?![ih])', line)
            if re.search("<i>", line[0]):
               line = re.split("</h4>", line[1])
               line = line[0].strip()
            else:
               line = re.split("&sdot;", line[0])
               line = line[1].strip()
            blume["name_de"] = line
      fi.close()

   # Read thumbnail name
   if thumbs and not blume["thumb"]:
      blume["thumb"] = thumbs[0]
       
   # Read image names
   if not blume["images"]:
      if htmls:
         fi = open(os.path.join(basename, htmls[0]), "rt")
         htmlimages = []
         for line in fi:
            if re.search("img", line) and re.search("src", line) and not re.search("<!--", line):
               line = re.split('src="|" ', line)
               htmlimages.append(line[1])   
         fi.close()
         if htmlimages:
            blume["images"] = [Record({"src": image}, ImageFields) for image in htmlimages]
      else:
         blume["images"] = [Record({"src": image}, ImageFields) for image in imagefiles]

   if len(blume["images"]) < len(imagefiles)-1:
      images = [i["src"] for i in blume["images"]]
      for image in imagefiles:
         if image in images: continue
         blume["images"].append(Record({"src": image}, ImageFields))
      
   # Read date and location
   if not blume["date"]:
      if htmls:
         fi = open(os.path.join(basename, htmls[0]), "rt")
         for line in fi:
            if re.search("<h4>", line) and re.search("[0-9]\.(20)?[01][0-9]", line):
               line = re.split('/', line, 1)
               blume["date"] = re.split("<h4>", line[0])[1].strip()
               blume["location"] = re.split("</h4>", line[1])[0].strip()
         fi.close()
      elif blume["images"]:
         st = os.stat(os.path.join(basename, blume["images"][0]["src"]))
         blume["date"] = time.strftime("%m.%Y", time.gmtime(st.st_mtime))

      if "date" in blume and len(blume["date"])>1:
         if blume["date"][0] == '0':
            blume["date"] = blume["date"][1:]

   # Return data
   return blume


#=====================================================================

# Call main function
main()
