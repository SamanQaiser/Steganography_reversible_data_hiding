import os
import cv2
import json
import numpy as np
from .apdh import APDH as apdh
from pathlib import Path

import genericflaskwebapp as app

class UserImage:
   class ERROR:
      NONE = None
      IMAGE_CREATION_FAILURE = 'Image creation failure'
      INVALID_IMAGE  = 'Invalid Image'
      IMAGE_DELETION_FAILURE = 'Image deletion failure'
      IMAGE_DECRYPTION_FAILURE = 'Image decryption failure'
      IMAGE_STORAGE_FAILURE = 'Image storage failure'
      INCOMPLETE_DETAILS = 'Incomplete details'
      INVALID_IMGEID = 'Invalid imageid'
      IMAGE_DOES_NOT_EXISTS = 'Image does not exists'
      IMAGES_NOT_FOUND = 'Images not found'
   
   class StoragePath:
      e_image = (Path(__file__).parent.parent.parent / 'storage' / (
         'encrypted_embedded'
      )).resolve()
      random_set = (Path(__file__).parent.parent.parent / 'storage' / (
         'random_set'
      )).resolve()
      ti = (Path(__file__).parent.parent.parent / 'storage' / (
         'ti'
      )).resolve()
      
      def resolve (basepath, filename):
         path = os.path.abspath((basepath / filename).resolve())
         
         return path
   
   def _read_image (imagefile):
      imagefile.seek(0)
      image = cv2.imdecode(
         np.asarray(
            bytearray(imagefile.read()),
            dtype=np.uint8,
         ),
         cv2.IMREAD_GRAYSCALE,
      ).astype(object).astype(np.uint8)
      
      return image
   
   def _encrypt_image (imagefile, data, base_name):
      data = str(data).strip()
      image = UserImage._read_image(imagefile)
      key_private = np.random.randint(40, 200)
      key_public = np.random.randint(40, 200)
      image_embedded_encrypted, data, bpp, Ti, random_set = apdh.encrypt(
         image,
         key_private,
         key_public,
         data,
      )
      
      cv2.imwrite(
         UserImage.StoragePath.resolve(
            UserImage.StoragePath.e_image,
            '{0}.png'.format(base_name),
         ),
         image_embedded_encrypted,
      )
      cv2.imwrite(
         UserImage.StoragePath.resolve(
            UserImage.StoragePath.random_set,
            '{0}.png'.format(base_name),
         ),
         random_set,
      )
      with open(
         UserImage.StoragePath.resolve(
            UserImage.StoragePath.ti,
            '{0}.json'.format(base_name),
         ),
         'w',
      ) as fh:
         fh.write(json.dumps(
            {
               'Ti': [
                  [int(Ti[0][0]), int(Ti[0][1])],
                  [int(Ti[1][0]), int(Ti[1][1])],
                  [int(Ti[2][0]), int(Ti[2][1])],
               ],
            },
         ))
      
      image_embedded_encrypted = np.array(
         cv2.imencode('.png', image_embedded_encrypted)[-1]
      ).tobytes()
      
      return (
         image_embedded_encrypted,
         data, bpp,
         (key_private, key_public,),
      )
   
   def _decrypt_image (
      base_name,
      bpp,
      keys_cryptography,
   ):
      image = cv2.imread(
         UserImage.StoragePath.resolve(
            UserImage.StoragePath.e_image,
            '{0}.png'.format(base_name),
         ),
         cv2.IMREAD_GRAYSCALE,
      ).astype(object).astype(np.uint8)
      random_set = cv2.imread(
         UserImage.StoragePath.resolve(
            UserImage.StoragePath.random_set,
            '{0}.png'.format(base_name),
         ),
         cv2.IMREAD_GRAYSCALE,
      ).astype(object).astype(np.uint8)
      with open(
         UserImage.StoragePath.resolve(
            UserImage.StoragePath.ti,
            '{0}.json'.format(base_name),
         ),
         'r',
      ) as fh:
         Ti = (json.loads(fh.read())).get('Ti')
      
      image_recovered, data_recovered = apdh.decrypt(
         image,
         bpp,
         Ti,
         random_set,
         keys_cryptography[0],
         keys_cryptography[1],
      )
      
      image_recovered = np.array(
         cv2.imencode('.png', image_recovered)[-1]
      ).tobytes()
      
      return (image_recovered, data_recovered)
   
   def load (userimage):
      if (app.backend.functionality.ImageStorage.is_decrypted(
         userimage.imageid,
      )):
         return app.backend.functionality.ImageStorage.get_available(
            imageid=userimage.imageid,
         )
      
      token = app.backend.functionality.ImageStorage.get_available(
         userimage.imageid,
      )
      
      if (token):
         return token
      
      if (os.path.isfile(UserImage.StoragePath.resolve(
         UserImage.StoragePath.e_image,
         '{0}.png'.format(userimage.basename),
      ))):
         image = np.array(
            cv2.imencode(
               '.png',
               cv2.imread(
                  UserImage.StoragePath.resolve(
                     UserImage.StoragePath.e_image,
                     '{0}.png'.format(userimage.basename),
                  ),
                  cv2.IMREAD_GRAYSCALE,
               ).astype(object).astype(np.uint8),
            )[-1]
         ).tobytes()
         
         return app.backend.functionality.ImageStorage.insert(
            userimage.imageid,
            image,
            decrypted=False,
         )
      
      return None
   
   def create (username, imagefile, data):
      if (not username ):
         return (None, UserImage.ERROR.INCOMPLETE_DETAILS)
      
      username = str(username).strip()
      data = str(data or '').strip()
      
      try:
         userimage = app.database.models.UserImage(
            dbengine=app.database.engine,
            username=username,
         )
         userimage.save()
         userimage = app.database.models.UserImage.get_images(
            username=username,
         )[-1]
      except:
         if (userimage):
            try:
               userimage.delete()
            except:
               pass
         
         userimage = None
      
      if (not userimage):
         return (None, UserImage.ERROR.IMAGE_CREATION_FAILURE)
      
      base_name = '{0}_{1}'.format(
         userimage.imageid,
         username,
      )
      
      try:
         image, data, bpp, keys_cryptography = UserImage._encrypt_image(
            imagefile, data, base_name,
         )
      except:
         try:
            userimage.delete()
         except:
            pass
         
         return (None, UserImage.ERROR.INVALID_IMAGE)
      
      userimage.basename = base_name
      userimage.bpp = bpp
      userimage.key0 = keys_cryptography[0]
      userimage.key1 = keys_cryptography[1]
      
      try:
         userimage.save()
      except:
         try:
            userimage.delete()
         except:
            pass
         
         return (None, UserImage.ERROR.IMAGE_STORAGE_FAILURE)
      
      return (True, userimage, (image, data))
   
   def decrypt (userimage):
      try:
         image, data = UserImage._decrypt_image(
            userimage.basename,
            userimage.bpp,
            (int(userimage.key0), int(userimage.key1),),
         )
      except:
         return (None, UserImage.ERROR.IMAGE_DECRYPTION_FAILURE)
      
      app.backend.functionality.ImageStorage.insert(
         imageid=userimage.imageid,
         imagebytes=image,
         decrypted=True,
         data=data,
      )
      
      return (True, (image, str(data).strip(),))
   
   def delete (username=None, imageid=None):
      if ((username or imageid) is None):
         return (None, UserImage.ERROR.INCOMPLETE_DETAILS)
      
      if (username):
         username = str(username).strip()
      
      if (imageid is not None):
         try:
            imageid = int(imageid)
         except:
            return (None, UserImage.ERROR.INVALID_IMAGEID)
      
      searchdata = dict()
      
      findall = False
      
      if (username):
         searchdata['username'] = username
         findall = True
      else:
         searchdata['imageid'] = imageid
      
      images = app.database.models.UserImage.get_images(
         **searchdata,
      )
      
      if ((not images) and (not findall)):
         return (None, UserImage.ERROR.IMAGE_DOES_NOT_EXISTS)
      
      if (not images):
         return (None, UserImage.ERROR.IMAGES_NOT_FOUND)
      
      if (not findall):
         images = [images,]
      
      for image in images:
         base_name = image.basename
         app.backend.functionality.ImageStorage.free(imageid=image.imageid)
         try:
            image.delete()
            
            try:
               os.remove(
                  UserImage.StoragePath.resolve(
                     UserImage.StoragePath.e_image,
                     '{0}.png'.format(base_name),
                  ),
               )
            except: pass
            
            try:
               os.remove(
                  UserImage.StoragePath.resolve(
                     UserImage.StoragePath.random_set,
                     '{0}.png'.format(base_name),
                  ),
               )
            except: pass
            
            try:
               os.remove(
                  UserImage.StoragePath.resolve(
                     UserImage.StoragePath.ti,
                     '{0}.json'.format(base_name),
                  ),
               )
            except: pass
         except:
            return (None, UserImage.ERROR.IMAGE_DELETION_FAILURE)
      
      return (True, UserImage.ERROR.NONE)
