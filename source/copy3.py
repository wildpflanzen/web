import os
import shutil




def subpaths(paths, limit=0):
   subpaths = []
   for p in paths:
      if os.path.isfile(p):
         continue
      files = os.listdir(p)
      if p == '.': p = ''
      else: p=p + '/'
      subpath = [p+sp for sp in files if os.path.isdir(p+sp)]
      if limit:
         subpath = subpath[:limit]
      subpaths = subpaths + subpath
   return subpaths


def mkdir(path):
   path = path.replace('\\', '/').split('/')
   allpath = '.'
   while path:
      allpath = allpath + '/'+ path[0]
      path = path[1:]
      if not os.path.isdir(allpath):
         os.mkdir(allpath)

   
def main():
   subs = subpaths(subpaths(subpaths('.')), limit=3)

   for s in subs:
      files = os.listdir(s)
      mkdir('copy/' + s)
      for f in files:
         shutil.copy2(s+'/'+f, 'copy/'+s+'/'+f)
         print('copy/'+s+'/'+f)
      input('enter')

main()
