import genericflaskwebapp as app

class UserImage (app.database.modelenginebridge.models.Model):
   modelname = 'UserImages'
   
   # imageid, username, basename, bpp, key0, key1
   imageid = app.database.modelenginebridge.models.Fields.Int(
      main=True,
      autoincrement=True,
   )
   
   username = app.database.modelenginebridge.models.Fields.Str(
      notnone=True,
   )
   basename = app.database.modelenginebridge.models.Fields.Str()
   bpp = app.database.modelenginebridge.models.Fields.Int()
   key0 = app.database.modelenginebridge.models.Fields.Int()
   key1 = app.database.modelenginebridge.models.Fields.Int()
   
   '''
   imagename = app.database.modelenginebridge.models.Fields.Str(
      notnone=True,
   )
   
   encryptionkey = app.database.modelenginebridge.models.Fields.Str(
      notnone=False,
   )
   
   decryptionkey = app.database.modelenginebridge.models.Fields.Str(
      notnone=False,
   )
   
   encrypted = app.database.modelenginebridge.models.Fields.Int()
   dataembedded = app.database.modelenginebridge.models.Fields.Int()
   '''
   
   def _set_username (self, username=None):
      if (not username):
         username = ''
      
      return (str(username).strip())
   
   def _set_basename (self, basename=None):
      if (not basename):
         basename = ''
      
      return (str(basename).strip())
   
   def _set_bpp (self, bpp=None):
      if (not bpp):
         bpp = 0
      
      return (int(bpp))
   
   def _set_key0 (self, key0=None):
      if (not key0):
         key0 = 0
      
      return (int(key0))
   
   def _set_key1 (self, key1=None):
      if (not key1):
         key1 = 0
      
      return (int(key1))
   
   '''
   def _set_encryptionkey (self, encryptionkey=None):
      if (not encryptionkey):
         encryptionkey = ''
      
      return (str(encryptionkey).strip())
   
   def _set_decryptionkey (self, decryptionkey=None):
      if (not decryptionkey):
         decryptionkey = ''
      
      return (str(decryptionkey).strip())
   
   def _set_encrypted (self, encrypted=None):
      encrypted = (
         1
         if (encrypted)
         else
         0
      )
      
      return encrypted
   
   def _set_dataembedded (self, dataembedded=None):
      dataembedded = (
         1
         if (dataembedded)
         else
         0
      )
      
      return dataembedded
   
   def _set_name (self, name=None):
      if (not name):
         return ''
      
      return (str(name).strip())
   
   def _set_password (self, password=None):
      if (not password):
         password = ''
      
      password = app.backend.security.passwordhasher.hash_password(
         password,
      )
      
      return password
   
   def check_password (self, password):
      result = app.backend.security.passwordhasher.hash_verify(
         password, self.password,
      )
      
      if (result):
         return True
      
      return False
   
   @classmethod
   def get_user (cls, username):
      user = cls.find(username=str(username).strip())
      
      if (user):
         return user
      
      return None
   
   @classmethod
   def get_authenticated_user (cls, username, password):
      user = cls.get_user(username=username)
      
      if (user
         and user.check_password(password=password)
      ):
         return user
      
      return None
   '''
   
   @classmethod
   def get_images (cls, imageid=None, username=None):
      if (not (imageid or username)):
         return None
      
      if (imageid and username):
         return None
      
      searchdata = dict()
      if (username):
         searchdata['username'] = str(username).strip()
      else:
         searchdata['imageid'] = int(imageid)
      
      images = cls.find(
         findall=(
            True
            if (username)
            else
            False
         ),
         **searchdata,
      )
      
      if (images):
         return images
      
      return None
