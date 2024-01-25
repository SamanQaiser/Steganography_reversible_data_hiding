import os
import cv2
import random
import string
import numpy as np

class APDH:
   def _get_data_bpp (data, image_shape):
      if ((image_shape[0] * image_shape[1]) >= 40):
         data = '000{0}'.format(data)
      
      dsize = int(min(
         (len(data) * 8),
         (6 * image_shape[0] * image_shape[1]),
      ))
      datasize = int(dsize // 8)
      bpp = 2
      
      while (
         ((dsize / bpp) > (image_shape[0] * image_shape[1]))
         and (bpp < 6)
      ):
         bpp += 1
      
      if (bpp > 6):
         bpp = 6
      
      data = data[:datasize]
      
      return (data, bpp)
   
   def _data_to_binary (bpp, data, image_shape):
      if ((image_shape[0] * image_shape[1]) >= 40):
         data = data[3:]
      
      bindata = ''.join([
         format(ord(char), '08b')
         for char in data
      ])
      if ((image_shape[0] * image_shape[1]) >= 40):
         bindata = '{0}{1}'.format(
            format(len(data), '024b'),
            bindata,
         )
      
      data = list()
      i = 0
      
      while (i < len(bindata)):
         data.append(
            int(bindata[i:(i + bpp)], base=2)
         )
         i += bpp
      
      return data
   
   def _binary_to_data (data, image_shape):
      if ((image_shape[0] * image_shape[1]) >= 40):
         dlen = int(data[:24], base=2)
         data = data[24:]
      else:
         dlen = (len(data) // 8)
      
      converted_data = list()
      dataindex = 0
      
      while (dataindex < len(data)):
         idata = int(data[dataindex:(dataindex + 8)], base=2)
         if (idata
            and (idata > 31)
            and (chr(idata) in string.printable)
         ):
            converted_data.append(
               chr(idata), # (int(data[dataindex:(dataindex + 8)], base=2)),
            )
         dataindex += 8
      
      data = ''.join(converted_data)
      data = data[:dlen]
      '''
      data = ''.join([
         chr(c_data)
         for c_data in converted_data
         if (c_data
            and (c_data > 31)
            and (chr(c_data) in string.printable)
         )
      ])
      '''
      
      return data
   
   def _image_to_blocks (image):
      if (image.shape[0] % 2):
         image = np.vstack([
               image,
               np.zeros(
                  ((image.shape[0] % 2), image.shape[1]),
                  dtype=np.uint8,
               ) + image[-1, :],
            ],
            dtype=np.uint8,
         )
      
      if (image.shape[1] % 2):
         image = np.hstack([
               image,
               np.zeros(
                  (image.shape[0], (image.shape[1] % 2)),
                  dtype=np.uint8,
               ) + image[:, -1],
            ],
            dtype=np.uint8,
         )
      
      rows_0 = image[0::2]
      rows_1 = image[1::2]
      rows = list()
      for row_0, row_1 in zip(rows_0, rows_1):
         cols_00 = row_0[0::2]
         cols_01 = row_0[1::2]
         cols_10 = row_1[0::2]
         cols_11 = row_1[1::2]
         cols = list()
         for col_00, col_01, col_10, col_11 in zip(
            cols_00, cols_01, cols_10, cols_11,
         ):
            cols.append([
               [col_00, col_01,],
               [col_10, col_11,],
            ])
         rows.append(cols)
      
      image = np.array(rows, dtype=np.uint8)
      
      return image
   
   def _blocks_to_image (image_blocks):
      image = np.concatenate(image_blocks, axis=1, dtype=np.uint8)
      image = np.concatenate(image, axis=1, dtype=np.uint8)
      
      return image
   
   def _random_block_inflate (block):
      inflatedblock = np.array([
            [
               np.full(
                  (2, 2),
                  column,
                  dtype=np.uint8,
               )
               for column in row
            ]
            for row in block
         ],
         dtype=np.uint8,
      )
      
      return inflatedblock
   
   def _get_random_key (shape):
      key = np.random.randint(40, 200, shape, dtype=np.uint8)
      
      return key
   
   def _single_encrypt (blocks, key_private, key_public):
      blocks += (key_private * key_public)
      
      return blocks
   
   def _single_decrypt (blocks, key_private, key_public):
      blocks -= (2 * key_private * key_public)
      
      return blocks
   
   def _image_encrypt (
      image,
      key_private,
      key_public,
   ):
      blocks = APDH._image_to_blocks(image)
      random_set = APDH._get_random_key(blocks.shape[:2])
      randoms = APDH._random_block_inflate(
         APDH._single_encrypt(
            random_set.copy(),
            key_private,
            key_public,
         ),
      )
      
      image_encrypted = APDH._single_encrypt(
         blocks,
         key_private,
         key_public,
      )
      image_encrypted += randoms
      
      return (image_encrypted, random_set)
   
   def _secret_embed (
      image_encrypted,
      data,
   ):
      data, bpp = APDH._get_data_bpp(data, image_encrypted.shape[:2])
      if ((image_encrypted.shape[0] * image_encrypted.shape[1]) >= 40):
         data_embedded = data[3:]
      else:
         data_embedded = data
      data = APDH._data_to_binary(bpp, data, image_encrypted.shape[:2])
      
      dataindex = 0
      shiftvalue = ((2 ** bpp) - 1)
      
      D1 = np.array(
         (image_encrypted[:, :, 0, 0] - image_encrypted[:, :, 1, 0]),
         dtype=np.uint8,
      )
      D1 = np.where(
         (D1 >= 128),
         (np.invert(D1) + 1),
         D1,
      )
      T1 = max(
         np.asarray(np.unique(D1, return_counts=True)).T,
         key=(lambda x: x[1]),
      )
      
      for sb_index, super_block in enumerate(image_encrypted): # row
         for b_index, block in enumerate(super_block): # col
            if (D1[sb_index, b_index] > T1[0]):
               if (block[0, 0] <= block[1, 0]):
                  block[1, 0] += shiftvalue
               else:
                  block[1, 0] -= shiftvalue
            elif (D1[sb_index, b_index] == T1[0]):
               if (block[0, 0] <= block[1, 0]):
                  if (dataindex < len(data)):
                     block[1, 0] += data[dataindex]
                     dataindex += 1
               else:
                  if (dataindex < len(data)):
                     block[1, 0] -= data[dataindex]
                     dataindex += 1
      
      D2 = np.array(
         (image_encrypted[:, :, 0, 1] - image_encrypted[:, :, 1, 1]),
         dtype=np.uint8,
      )
      D2 = np.where(
         (D2 >= 128),
         (np.invert(D2) + 1),
         D2,
      )
      T2 = max(
         np.asarray(np.unique(D2, return_counts=True)).T,
         key=(lambda x: x[1]),
      )
      
      for sb_index, super_block in enumerate(image_encrypted): # row
         for b_index, block in enumerate(super_block): # col
            if (D2[sb_index, b_index] > T2[0]):
               if (block[0, 1] <= block[1, 1]):
                  block[1, 1] += shiftvalue
               else:
                  block[1, 1] -= shiftvalue
            elif (D2[sb_index, b_index] == T2[0]):
               if (block[0, 1] <= block[1, 1]):
                  if (dataindex < len(data)):
                     block[1, 1] += data[dataindex]
                     dataindex += 1
               else:
                  if (dataindex < len(data)):
                     block[1, 1] -= data[dataindex]
                     dataindex += 1
      
      D3 = np.array(
         (image_encrypted[:, :, 0, 0] - image_encrypted[:, :, 0, 1]),
         dtype=np.uint8,
      )
      D3 = np.where(
         (D3 >= 128),
         (np.invert(D3) + 1),
         D3,
      )
      T3 = max(
         np.asarray(np.unique(D3, return_counts=True)).T,
         key=(lambda x: x[1]),
      )
      
      for sb_index, super_block in enumerate(image_encrypted): # row
         for b_index, block in enumerate(super_block): # col
            if (D3[sb_index, b_index] > T3[0]):
               if (block[0, 0] <= block[0, 1]):
                  block[0, 1] += shiftvalue
               else:
                  block[0, 1] -= shiftvalue
            elif (D3[sb_index, b_index] == T3[0]):
               if (block[0, 0] <= block[0, 1]):
                  if (dataindex < len(data)):
                     block[0, 1] += data[dataindex]
                     dataindex += 1
               else:
                  if (dataindex < len(data)):
                     block[0, 1] -= data[dataindex]
                     dataindex += 1
      
      return (
         image_encrypted, # as image_embedded
         data_embedded,
         bpp,
         (T1, T2, T3),
      )
   
   def _secret_extract (
      image_embedded_encrypted,
      bpp,
      Ti,
   ):
      image_embedded = APDH._image_to_blocks(image_embedded_encrypted)
      shiftvalue = ((2 ** bpp) - 1)
      
      secret3 = list()
      secret2 = list()
      secret1 = list()
      
      D3 = np.array(
         (image_embedded[:, :, 0, 0] - image_embedded[:, :, 0, 1]),
         dtype=np.uint8,
      )
      D3 = np.where(
         (D3 >= 128),
         (np.invert(D3) + 1),
         D3,
      )
      T3 = Ti[2]
      
      for sb_index, super_block in enumerate(image_embedded): # row
         for b_index, block in enumerate(super_block): # col
            if ((T3[0] <= D3[sb_index, b_index])
               and (D3[sb_index, b_index] <= (T3[0] + shiftvalue))
            ):
               secret = (D3[sb_index, b_index] - T3[0])
               secret3.append(secret)
               
               if (block[0, 0] <= block[0, 1]):
                  block[0, 1] -= secret
               elif (block[0, 0] > block[0, 1]):
                  block[0, 1] += secret
            elif (D3[sb_index, b_index] > (T3[0] + shiftvalue)):
               if (block[0, 0] <= block[0, 1]):
                  block[0, 1] -= shiftvalue
               elif (block[0, 0] > block[0, 1]):
                  block[0, 1] += shiftvalue
      
      D2 = np.array(
         (image_embedded[:, :, 0, 1] - image_embedded[:, :, 1, 1]),
         dtype=np.uint8,
      )
      D2 = np.where(
         (D2 >= 128),
         (np.invert(D2) + 1),
         D2,
      )
      T2 = Ti[1]
      
      for sb_index, super_block in enumerate(image_embedded): # row
         for b_index, block in enumerate(super_block): # col
            if ((T2[0] <= D2[sb_index, b_index])
               and (D2[sb_index, b_index] <= (T2[0] + shiftvalue))
            ):
               secret = (D2[sb_index, b_index] - T2[0])
               secret2.append(secret)
               
               if (block[0, 1] <= block[1, 1]):
                  block[1, 1] -= secret
               elif (block[0, 1] > block[1, 1]):
                  block[1, 1] += secret
            elif (D2[sb_index, b_index] > (T2[0] + shiftvalue)):
               if (block[0, 1] <= block[1, 1]):
                  block[1, 1] -= shiftvalue
               elif (block[0, 1] > block[1, 1]):
                  block[1, 1] += shiftvalue
      
      D1 = np.array(
         (image_embedded[:, :, 0, 0] - image_embedded[:, :, 1, 0]),
         dtype=np.uint8,
      )
      D1 = np.where(
         (D1 >= 128),
         (np.invert(D1) + 1),
         D1,
      )
      T1 = Ti[0]
      
      for sb_index, super_block in enumerate(image_embedded): # row
         for b_index, block in enumerate(super_block): # col
            if ((T1[0] <= D1[sb_index, b_index])
               and (D1[sb_index, b_index] <= (T1[0] + shiftvalue))
            ):
               secret = (D1[sb_index, b_index] - T1[0])
               secret1.append(secret)
               
               if (block[0, 0] <= block[1, 0]):
                  block[1, 0] -= secret
               elif (block[0, 0] > block[1, 0]):
                  block[1, 0] += secret
            elif (D1[sb_index, b_index] > (T1[0] + shiftvalue)):
               if (block[0, 0] <= block[1, 0]):
                  block[1, 0] -= shiftvalue
               elif (block[0, 0] > block[1, 0]):
                  block[1, 0] += shiftvalue
      
      secret3 = ''.join([
         format(s3, '0{0}b'.format(bpp))
         for s3 in secret3
      ])
      secret2 = ''.join([
         format(s2, '0{0}b'.format(bpp))
         for s2 in secret2
      ])
      secret1 = ''.join([
         format(s1, '0{0}b'.format(bpp))
         for s1 in secret1
      ])
      
      secret = '{0}{1}{2}'.format(secret1, secret2, secret3)
      secret = '{1}{0}'.format(('0' * ((8 - (len(secret) % 8)) % 8)), secret)
      
      data = APDH._binary_to_data(secret, image_embedded.shape[:2])
      
      return (image_embedded, data) # as image_encrypted
   
   def _image_decrypt (
      blocks,
      random_set,
      key_private,
      key_public,
   ):
      randoms = APDH._random_block_inflate(
         random_set.copy(),
      )
      
      image = APDH._single_decrypt(
         blocks,
         key_private,
         key_public,
      )
      image -= randoms
      
      return image
   
   def encrypt (
      image,
      key_private,
      key_public,
      data,
   ):
      image_encrypted, random_set = APDH._image_encrypt(
         image.copy(),
         key_private,
         key_public,
      )
      image_embedded_encrypted, data, bpp, Ti = APDH._secret_embed(
         image_encrypted,
         data,
      )
      image_embedded_encrypted = APDH._blocks_to_image(
         image_embedded_encrypted,
      )
      
      return (image_embedded_encrypted, data, bpp, Ti, random_set)
   
   def decrypt (
      image_embedded_encrypted,
      bpp,
      Ti,
      random_set,
      key_private,
      key_public,
   ):
      image_encrypted, data = APDH._secret_extract(
         image_embedded_encrypted.copy(),
         bpp,
         Ti,
      )
      image = APDH._blocks_to_image(
         APDH._image_decrypt(
            image_encrypted,
            random_set,
            key_private,
            key_public,
         )
      )
      
      return (image, data)

if __name__ == '__main__':
   image_path = input('Path to image (any): ')
   image_path = os.path.abspath(image_path)
   
   if (not os.path.isfile(image_path)):
      print('Invalid file path !')
      exit(0)
   
   data = input('Data to embed in image: ').strip()
   
   image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE).astype(
      object
   ).astype(np.uint8)
   
   key_private = np.random.randint(40, 200) # key private
   key_public = np.random.randint(40, 200) # key public
   
   # Encryption
   print('Encrypting', end='\r')
   image_embedded_encrypted, data, bpp, Ti, random_set = APDH.encrypt(
      image,
      key_private,
      key_public,
      data,
   )
   print('\rEncrypted !\n')
   
   print('Data embedded in image: \'{0}\' ({1})\n'.format(data, len(data)))
   
   # Decryption
   print('Decrypting', end='\r')
   image_recovered, data_recovered = APDH.decrypt(
      image_embedded_encrypted,
      bpp,
      Ti,
      random_set,
      key_private,
      key_public,
   )
   print('\rDecrypted !\n')
   
   print(
      'Image recovery accuracy:',
      round((np.mean(image == image_recovered) * 100), ndigits=2),
   )
   
   print('Data recovered from image: \'{0}\' ({1})'.format(
      data_recovered, len(data_recovered),
   ))
   
   print('\nDisplaying images')
   
   print('Encrypted Image opened in new window.\nPress any key to close.')
   cv2.imshow('Embedded Encrypted Image', image_embedded_encrypted)
   cv2.waitKey(0)
   cv2.destroyWindow('Embedded Encrypted Image')
   
   print('\nDecrypted Image opened in new window.\nPress any key to close.')
   cv2.imshow('Recovered Image', image_recovered)
   cv2.waitKey(0)
   cv2.destroyWindow('Recovered Image')
   
   print('Done !')
