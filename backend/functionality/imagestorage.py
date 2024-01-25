import genericflaskwebapp as app

class ImageStorage:
   tokens = dict()
   images = dict()
   decrypted = dict()
   data = dict()
   
   def get_data (imageid=None, token=None):
      if (token is not None):
         imageid = (
            ImageStorage.tokens.get(token)
            if (ImageStorage.tokens.get(token) is not None)
            else
            imageid
         )
      
      data = str(ImageStorage.data.get(imageid) or '').strip()
      
      return data
   
   def is_decrypted (imageid=None, token=None):
      if (token is not None):
         imageid = (
            ImageStorage.tokens.get(token)
            if (ImageStorage.tokens.get(token) is not None)
            else
            imageid
         )
      
      result = (ImageStorage.decrypted.get(imageid) or False)
      
      return result
   
   def get_available (imageid):
      if (imageid is None):
         return None
      
      tokens = [
         token
         for token, imgid in ImageStorage.tokens.items()
         if (imgid == imageid)
      ][:1]
      
      if (tokens):
         return tokens[0]
      
      return None
   
   def insert (imageid, imagebytes, decrypted=False, data=None):
      token = ImageStorage.get_available(imageid) or None
      
      if (not token):
         while ((token in ImageStorage.tokens.keys()) or (not token)):
            token = app.backend.security.basickeygen.key_general_generate(
               length=16,
            )
      
      ImageStorage.tokens[token] = imageid
      ImageStorage.images[imageid] = imagebytes
      ImageStorage.decrypted[imageid] = decrypted
      ImageStorage.data[imageid] = (data or '')
      
      return token
   
   def free (token=None, imageid=None):
      if ((imageid or token) is None):
         return None
      
      if (imageid is not None):
         try:
            imageid = int(imageid)
         except:
            imageid = None
      
      if (imageid is not None):
         try:
            ImageStorage.images.pop(imageid)
         except:
            pass
         
         try:
            ImageStorage.decrypted.pop(imageid)
         except:
            pass
         
         try:
            ImageStorage.data.pop(imageid)
         except:
            pass
         
         attachedtokens = [
            itoken
            for itoken, iid in ImageStorage.tokens.items()
            if (iid == imageid)
         ]
         
         for atokens in attachedtokens:
            try:
               ImageStorage.tokens.pop(atokens)
            except:
               pass
      
      if (token is not None):
         try:
            imageid = ImageStorage.tokens.pop(token)
            
            try:
               ImageStorage.images.pop(imageid)
            except:
               pass
            
            try:
               ImageStorage.data.pop(imageid)
            except:
               pass
            
            ImageStorage.decrypted.pop(imageid)
         except:
            pass
      
      return True
   
   def retrieve (token):
      imageid = ImageStorage.tokens.get(token)
      
      imagebytes = ImageStorage.images.get(imageid)
      
      return imagebytes
