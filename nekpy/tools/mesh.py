def factor(number):
    """Factor number, return list of factors"""
    factors = []
    n = int(number)
    test = 2
    while n >= test:
        if int((n/test))*test == n:
            n /= test
            factors.insert(0,test)
        else:
            test += 1
 
    if n != 1:
        print("Something is up: ", number, factors)
 
    return factors

def get_ind(ix, iy, iz, n):
    """Compute 1-based index of element corner"""
    return int(1 + (ix%n[0]) + (iy%n[1]) * n[0] + (iz%n[2]) * n[0] * n[1])

def uniform_profile(ind, num, start, end):
    """Return uniformly spaced mesh corners"""
    delta = (end - start) / num
    return start + ind * delta, delta

def pick_profile(prof):
    """Pick 1D profile type"""
    if prof == "uniform":
        return uniform_profile
    return None

class Mesh:

  def __init__(self, root, corner, n, boundaries, 
               profile_x = 'uniform',
               profile_y = 'uniform',
               profile_z = 'uniform'):
    """Store data in an object"""
    import numpy as np
    self.root = np.array(root, dtype=np.float64)
    self.corner = np.array(corner, dtype=np.float64)
    self.n = np.array(n, dtype=np.int32)
    self.boundaries = boundaries
    self.extent = self.corner - self.root
    self.delta = self.extent / self.n
    self.vertices = None
    self.faces = None
    self.element_bounds = None
    self.elements = None
    self.map = None

    self.profile_x = pick_profile(profile_x)
    self.profile_y = pick_profile(profile_y)
    self.profile_z = pick_profile(profile_z)

    return

  def generate_elements(self):
    """Generate list of element corners for the rea file"""
    import numpy as np
    self.elements = np.zeros((np.prod(self.n), 24), dtype=np.float64)  
    e_root = np.array([0.,0.,0.], dtype=np.float64)
    delta  = np.array([0.,0.,0.], dtype=np.float64)
    e = 0
    for iz in range(self.n[2]):
      e_root[2], delta[2] = self.profile_z(iz, self.n[2], self.root[2], self.corner[2])
      for iy in range(self.n[1]):
        e_root[1], delta[1] = self.profile_y(iy, self.n[1], self.root[1], self.corner[1])
        for ix in range(self.n[0]):
          e_root[0], delta[0] = self.profile_x(ix, self.n[0], self.root[0], self.corner[0])

          self.elements[e,0]  = e_root[0]
          self.elements[e,1]  = e_root[0] + delta[0]
          self.elements[e,2]  = e_root[0] + delta[0]
          self.elements[e,3]  = e_root[0]
                              
          self.elements[e,4]  = e_root[1]
          self.elements[e,5]  = e_root[1]
          self.elements[e,6]  = e_root[1] + delta[1]
          self.elements[e,7]  = e_root[1] + delta[1]
                              
          self.elements[e,8]  = e_root[2]
          self.elements[e,9]  = e_root[2]
          self.elements[e,10] = e_root[2]
          self.elements[e,11] = e_root[2]

          self.elements[e,12] = e_root[0]
          self.elements[e,13] = e_root[0] + delta[0]
          self.elements[e,14] = e_root[0] + delta[0]
          self.elements[e,15] = e_root[0]
                              
          self.elements[e,16] = e_root[1]
          self.elements[e,17] = e_root[1]
          self.elements[e,18] = e_root[1] + delta[1]
          self.elements[e,19] = e_root[1] + delta[1]
                              
          self.elements[e,20] = e_root[2] + delta[2]
          self.elements[e,21] = e_root[2] + delta[2]
          self.elements[e,22] = e_root[2] + delta[2]
          self.elements[e,23] = e_root[2] + delta[2]

          e = e + 1
    return

  def generate_faces(self):
    """Generate list of element faces for the rea file"""
    import numpy as np
    self.faces = np.zeros((np.prod(self.n),6, 2))
    self.element_bounds = []
    for e in range(self.elements.shape[0]):
      ix = int((self.elements[e,0] - self.root[0])/self.delta[0])
      iy = int((self.elements[e,4] - self.root[1])/self.delta[1])
      iz = int((self.elements[e,8] - self.root[2])/self.delta[2])

      self.faces[e,0,0] = (e+1)*10 + 1 
      if iy == 0:
        self.element_bounds.append(self.boundaries[0])
        self.faces[e,0,1] = 1 + ix + (self.n[1]-1) * self.n[0] + iz * self.n[0]*self.n[1]      
      else:
        self.element_bounds.append('E')
        self.faces[e,0,1] = 1 + ix + (iy - 1) * self.n[0] + iz * self.n[0]*self.n[1]      

      self.faces[e,1,0] = (e+1)*10 + 2
      if ix == self.n[0]-1:
        self.element_bounds.append(self.boundaries[1])
        self.faces[e,1,1] = 1 + iy * self.n[0] + iz * self.n[0]*self.n[1]      
      else:
        self.element_bounds.append('E')
        self.faces[e,1,1] = 1 + ix + 1 + iy * self.n[0] + iz * self.n[0]*self.n[1]      

      self.faces[e,2,0] = (e+1)*10 + 3 
      if iy == self.n[1]-1:
        self.element_bounds.append(self.boundaries[2])
        self.faces[e,2,1] = 1 + ix + iz * self.n[0]*self.n[1]      
      else:
        self.element_bounds.append('E')
        self.faces[e,2,1] = 1 + ix + (iy + 1) * self.n[0] + iz * self.n[0]*self.n[1]      

      self.faces[e,3,0] = (e+1)*10 + 4 
      if ix == 0:
        self.element_bounds.append(self.boundaries[3])
        self.faces[e,3,1] = 1 + self.n[0] - 1 + iy * self.n[0] + iz * self.n[0]*self.n[1]      
      else:
        self.element_bounds.append('E')
        self.faces[e,3,1] = 1 + ix - 1 + iy * self.n[0] + iz * self.n[0]*self.n[1]      

      self.faces[e,4,0] = (e+1)*10 + 5 
      if iz == 0:
        self.element_bounds.append(self.boundaries[4])
        self.faces[e,4,1] = 1 + ix + iy * self.n[0] + (self.n[2]-1) * self.n[0]*self.n[1]      
      else:
        self.element_bounds.append('E')
        self.faces[e,4,1] = 1 + ix + iy * self.n[0] + (iz-1) * self.n[0]*self.n[1]      

      self.faces[e,5,0] = (e+1)*10 + 6 
      if iz == self.n[2] - 1:
        self.element_bounds.append(self.boundaries[5])
        self.faces[e,5,1] = 1 + ix + iy * self.n[0]      
      else:
        self.element_bounds.append('E')
        self.faces[e,5,1] = 1 + ix + iy * self.n[0] + (iz+1) * self.n[0]*self.n[1]      

  def get_mesh_data(self):
    """Format element corners for the rea file"""
    import numpy as np
    letters = [chr(97+i) for i in range(26)] + [chr(65+i) for i in range(26)]
    mesh = " {:11d}  {:d} {:11d}           NEL,NDIM,NELV".format(np.prod(self.n), 3, np.prod(self.n))
    for e in range(self.elements.shape[0]):
      ix = int(np.rint((self.elements[e,0] - self.root[0])/self.delta[0]))
      iy = int(np.rint((self.elements[e,4] - self.root[1])/self.delta[1]))
      iz = int(np.rint((self.elements[e,8] - self.root[2])/self.delta[2]))
      mesh += "\n            ELEMENT {:11d} [{:5d}{:1s}]  GROUP  0\n".format(e+1, iz+1, letters[(ix+iy*self.n[0]) % 52]) 
      mesh += "  {: 13.10E}  {: 13.10E}  {: 13.10E}  {: 13.10E} \n".format(*(self.elements[e, 0: 4].tolist())) 
      mesh += "  {: 13.10E}  {: 13.10E}  {: 13.10E}  {: 13.10E} \n".format(*(self.elements[e, 4: 8].tolist())) 
      mesh += "  {: 13.10E}  {: 13.10E}  {: 13.10E}  {: 13.10E} \n".format(*(self.elements[e, 8:12].tolist())) 
      mesh += "  {: 13.10E}  {: 13.10E}  {: 13.10E}  {: 13.10E} \n".format(*(self.elements[e,12:16].tolist())) 
      mesh += "  {: 13.10E}  {: 13.10E}  {: 13.10E}  {: 13.10E} \n".format(*(self.elements[e,16:20].tolist())) 
      mesh += "  {: 13.10E}  {: 13.10E}  {: 13.10E}  {: 13.10E} ".format(*(self.elements[e,20:24].tolist())) 
    return mesh

  def get_fluid_boundaries(self):
    """Format element faces for rea file"""
    fluid_boundary = ""
    opposite_face = [3, 4, 1, 2, 6, 5]
    for e in range(self.elements.shape[0]):
      for f in range(6):
        fluid_boundary += " {:3s} {:d}   {:7.2f}        {:7f}       0.00000       0.00000       0.00000\n".format(
                            self.element_bounds[e*6+f], int(self.faces[e,f,0]), self.faces[e,f,1], opposite_face[f])
    return fluid_boundary[:-1]

  def set_map(self, target):
    """Generate element <-> process mapping for <target> mpi ranks"""
    import numpy as np

    tfac = factor(target)
    xfac = factor(self.n[0])
    yfac = factor(self.n[1])
    zfac = factor(self.n[2])
    xtot = int(np.prod(np.array(xfac)))
    ytot = int(np.prod(np.array(yfac)))
    ztot = int(np.prod(np.array(zfac)))

    queue = []

    while len(tfac) > 0:
      if len(set(tfac) & set(xfac)) == 0 :
        xtot = 0
      if len(set(tfac) & set(yfac)) == 0 :
        ytot = 0
      if len(set(tfac) & set(zfac)) == 0 :
        ztot = 0

      if ztot >= xtot and ztot >= ytot :
        split = (set(tfac) & set(zfac)).pop()
        queue.append((2,split))
        tfac.remove(split)
        zfac.remove(split)
        ztot /= split
      elif ytot >= xtot :
        split = (set(tfac) & set(yfac)).pop()
        queue.append((1,split))
        tfac.remove(split)
        yfac.remove(split)
        ytot /= split
      else : 
        split = (set(tfac) & set(xfac)).pop()
        queue.append((0,split))
        tfac.remove(split)
        xfac.remove(split)
        xtot /= split

    xtot = int(np.prod(np.array(xfac)))
    ytot = int(np.prod(np.array(yfac)))
    ztot = int(np.prod(np.array(zfac)))
    while len(xfac) + len(yfac) + len(zfac) > 0:
      if ztot >= xtot and ztot >= ytot :
        split = zfac.pop(0)
        queue.append((2,split))
        ztot /= split
      elif ytot >= xtot :
        split = yfac.pop(0)
        queue.append((1,split))
        ytot /= split
      else : 
        split = xfac.pop(0)
        queue.append((0,split))
        xtot /= split

    ind = np.zeros((np.prod(self.n), 4), dtype=np.uint32)
    for e in range(self.elements.shape[0]):
      ind[e,1] = np.rint((self.elements[e,0] - self.root[0])/self.delta[0])
      ind[e,2] = np.rint((self.elements[e,4] - self.root[1])/self.delta[1])
      ind[e,3] = np.rint((self.elements[e,8] - self.root[2])/self.delta[2])

    xfac = factor(self.n[0])
    yfac = factor(self.n[1])
    zfac = factor(self.n[2])
    xtot = int(np.prod(np.array(xfac)))
    ytot = int(np.prod(np.array(yfac)))
    ztot = int(np.prod(np.array(zfac)))
    for split in queue:
      if split[0] == 0:
        xtot /= split[1]
        ind[:,0] = split[1] * ind[:,0] + ind[:,1] / xtot
        ind[:,1] = ind[:,1] % xtot
      if split[0] == 1:
        ytot /= split[1]
        ind[:,0] = split[1] * ind[:,0] + ind[:,2] / ytot
        ind[:,2] = ind[:,2] % ytot
      if split[0] == 2:
        ztot /= split[1]
        ind[:,0] = split[1] * ind[:,0] + ind[:,3] / ztot
        ind[:,3] = ind[:,3] % ztot

    self.map = ind[:,0]

    return

  def get_map(self):
    """Format element <-> process mapping for map file"""
    import numpy as np
    map_data = "{:d} 0 {:d} {:d} {:d} 0 0\n".format(self.elements.shape[0], 
                                             self.n[0], self.n[1], self.n[2])

    my_n = np.copy(self.n)
    if not self.boundaries[0] == 'P':
      my_n[1] += 1
    if not self.boundaries[1] == 'P':
      my_n[0] += 1
    if not self.boundaries[5] == 'P':
      my_n[2] += 1

    for e in range(self.map.shape[0]):
      ix = np.rint((self.elements[e,0] - self.root[0])/self.delta[0])
      iy = np.rint((self.elements[e,4] - self.root[1])/self.delta[1])
      iz = np.rint((self.elements[e,8] - self.root[2])/self.delta[2])

      map_data += "{:d} {:d} {:d} {:d} {:d} {:d} {:d} {:d} {:d}\n".format(
                   self.map[e], 
                   get_ind(ix,   iy  , iz  , my_n),
                   get_ind(ix+1, iy  , iz  , my_n),
                   get_ind(ix,   iy+1, iz  , my_n),
                   get_ind(ix+1, iy+1, iz  , my_n),
                   get_ind(ix,   iy  , iz+1, my_n),
                   get_ind(ix+1, iy  , iz+1, my_n),
                   get_ind(ix,   iy+1, iz+1, my_n),
                   get_ind(ix+1, iy+1, iz+1, my_n))
     
    return map_data

