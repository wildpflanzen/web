# -*- coding: utf8 -*-
"""
   Simple Database management system.
   Class Database = list of records
   Class Record = dictionary with 'fields' and values

   Both clases have the variable 'fields' containing the list of sorted fields
   of database.

   LICENSE
   =======
   This source code was written by Carlos Pardo <carlos.tecnomail@gmail.com>,
   and is published under the following license:

   Copyright (c) Carlos Pardo, 2013

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

import json
import codecs
import os
import re


class DataBase:
   """
      DataBase management.
      Database is a list of Records (dicts):
      db = [
         { "name": "Charlie", "height": 150, "male": True },
         { "name": "Lola",    "height": 125, "male": False },
      ]

   """

   def __init__(self, db=[], fields=[]):
      """Inits database"""
      if type(db) == list:
         self.database = [Record(rec, fields) for rec in db]
         self.fields = fields[:]
      elif isinstance(db, DataBase):
         self.database = db.database
         if not fields:
            self.fields = db.fields
         else:
            self.fields = fields[:]
      else:
         raise TypeError("Database must be a list or DataBase. Bad argument type: " + str(db))


   def __iter__(self):
      """Return one by one, all record in database"""
      for record in self.database:
         yield record

         
   def __getitem__(self, n):
      """Returns n'th element of database"""
      if len(self.database)>n:
         return self.database[n]
      else:
         return None


   def __add__(self, db):
      if not db:
         return self
      elif isinstance(db, Record):
         return Database(self.database + [db], self.fields)
      elif isinstance(db, DataBase):
         return DataBase(self.database + db.database, self.fields)
      else:
         raise TypeError("Bad argument type:" + str(record))


   def __len__(self):
      """Return the number of records of database"""
      return len(self.database)

   
   def __repr__(self, indent=3):
      """Compute and return the 'oficial' string representation of database"""
      return json.dumps(self.database, indent=indent)


   def fieldsort(self, fields, relink = False):
      """Change list of sorted fields in a record.
         Every record in database points to this list"""
      if relink:
         # Change fields sort of database and all records
         self.fields = fields
         for record in self.database:
            record.fields = self.fields
      else:
         # Change fields sort of database in place 
         del self.fields[:]
         for i in fields:
            self.fields.append(i)

      
   def sort(self, field1, field2="", field3=""):
      """Sort in place database by field1, field2 and field3"""
      self.database = self.sorted(field1, field2, field3)


   def sorted(self, field1, field2="", field3=""):
      """Return a copy of database sorted by field1, field2 and field3"""
      if not self.database:
         return []
      newdb = []
      for record in self.database:
         allindex = u""
         for field in [field1, field2, field3]:
            if field in record:
               if type(record[field]) == type(1) or type(record[field]) == type(0.5):
                  num = u"%22.16e" % record[field]
                  num = num.split(u"e")
                  # Don't work for numbers greather than 9.99e+99 or less than 1.00e-99
                  allindex = allindex + num[1].strip(u"+ ") + num[0] 
               else:
                  allindex = allindex + unicode(record[field])
         newdb.append([allindex, record])
      newdb.sort(cmp=lambda x,y: cmp(x[0], y[0]))
      return [record[1] for record in newdb]
   

   def append(self, record):
      """Append records in database"""
      if not record:
         return
      elif isinstance(record, Record):
         self.database.append(record)
      elif isinstance(record, DataBase):
         self.database = self.database + record.database
      elif type(record) == dict:
         self.database.append(Record(record, self.fields))
      elif type(record) == list:
         self.database = self.database + [Record(item, self.fields) for item in record]
      else:
         raise TypeError("Bad argument type:" + str(record))


# ===================================================

class Record(dict):
   """
      Record of database management.
      Record is a dictionary with methods:
         { "name": "Lola",    "height": 125, "male": False }
   """
   
   def __init__(self, record={}, fields=[], indent=3):
      """Init record"""
      self.ShowEmptyFields = True  # Dumps all fields of self.fields, including non existing ones
      self.indent = indent
      if type(record) == str or type(record) == unicode:
         self.read(record)
         self.fields = fields
      elif type(record) == dict:
         if not record:
            self.record = record.copy()
         else:
            self.record = record
         self.fields = fields
      elif isinstance(record, Record):
         self.record = record.record
         self.fields = record.fields
      else:
         raise  TypeError("Record must be type Record or dictionary. Bad argument type: " + str(record))
      

   def __len__(self):
      """Return the number of fields in record"""
      return len(self.record)

   
   def __iter__(self):
      """Return one by one, all fields of a record, sorted"""
      for field in self.keys():
         yield field


   def iteritems(self):
      """Return one by one, all fields of a record, sorted"""
      for field in self.keys():
         yield field, self[field]

         
   def __getitem__(self, field, emptyfield=u""):
      """Returns field of a record or None if field don't exists"""
      if field in self.record:
         return self.record[field]
      elif field in self.fields:
         return emptyfield
      else:
         raise KeyError(field)


   def __delitem__(self, field):
      if field in self.record:
         del self.record[field]


   def __setitem__(self, field, data=u""):
      """Set field value to data"""
      if type(field) == str:
         field = unicode(field)
      if type(data) == str:
         data = unicode(data)
      self.record[field] = data


   def __contains__(self, item):
      """Test if item is a field of record"""
      if item in self.keys():
         return True
      return False
   
      
   def keys(self):
      """Return a list of fields in record sorted by self.fields list.
         If ShowEmptyFields is True, return nonexisting fields too"""
      fields = [f for f in self.fields if self.ShowEmptyFields or f in self.record]
      keys = [k for k in sorted(self.record.keys()) if not k in fields]
      return fields + keys


   def fieldsort(self, fields):
      """Change list of sorted fields in a record.
         Every record in database points to this list by default"""
      if isinstance(fields, list):
         self.fields = fields
      else:
         raise TypeError()


   def append(field, data=u""):
      """Alias for setitem"""     
      self.__setitem__(field, data)
      

   def __str__(self):
      return self.__repr__().encode("utf-8")

   
   def __unicode__(self):
      return self.__repr__()

   
   def __repr__(self):
      """Return string representation of a record.
         Returns all fields in self.fields even if it doesn't exist and
         all fields in the record even if they don't exist in self.fields"""
      # Compute a string representation of field
      return json.dumps(self, ensure_ascii=False, indent=self.indent)


   def write(self, filename):
      """Write Record data to file"""
      data = u"\ufeff".encode("utf-8") + self.__repr__().encode("utf-8")
      open(filename, "w").write(data)
      

   def read(self, filename):
      data = open(filename, "r").read()
      data = re.sub("\xff\xfe]*{", "{", data)
      try:
         data = data.decode("utf-8")
      except:
         data = data.decode("cp1252")
      if data[:1] == u"\ufeff":
         data = data[1:]
      data = re.sub(",[\n\r\t ]*}", " }", data)
      data = json.loads(data)     
      if not data or not isinstance(data, dict):
         raise TypeError("No data or invalid data type. Filename:" + filename)
      self.record = data


# ===================================================

def _test_database():
   """Test database module"""

   # -------------------------
   # Unicode and UTF-8
   # -------------------------
   print "\n---------------\n"
   rec = Record("r.txt")
   print rec
   rec = Record("u.txt")
   print rec


# ===================================================

if __name__ == "__main__":
   _test_database()
   
