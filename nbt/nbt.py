from struct import pack, unpack
from gzip import GzipFile

TAG_END = 0
TAG_BYTE = 1
TAG_SHORT = 2
TAG_INT = 3
TAG_LONG = 4
TAG_FLOAT = 5
TAG_DOUBLE = 6
TAG_BYTE_ARRAY = 7
TAG_STRING = 8
TAG_LIST = 9
TAG_COMPOUND = 10

class TAG(object):
	"""Each Tag needs to take a file-like object for reading and writing.
	The file object will be initialised by the calling code."""
	id = None
	
	def __init__(self, value=None, name=None):
		if name: self.name = TAG_String(name)
		else: self.name = None
		self.value = value
	
	#Parsers and Generators	
	def _parse_buffer(self, buffer):
		raise NotImplementedError(self.__class__.__name__)
	
	def _render_buffer(self, buffer, offset=None):
		raise NotImplementedError(self.__class__.__name__)
		
	#Printing and Formatting of tree
	def tag_info(self):
		return self.__class__.__name__ + \
			('("%s")' % self.name if (self.name and self.name.value) else "") + \
			": " + self.__str__()
	
	def pretty_tree(self, indent=0):
		return ("\t"*indent) + self.tag_info()
		
class _TAG_Numeric(TAG):
	def __init__(self, unpack_as, size, buffer=None, value=None, name=None):
		super(_TAG_Numeric, self).__init__(value, name)
		self.unpack_as = unpack_as
		self.size = size
		if buffer:
			self._parse_buffer(buffer)
	
	#Parsers and Generators	
	def _parse_buffer(self, buffer, offset=None):
		self.value = unpack(self.unpack_as, buffer.read(self.size))[0]
	
	def _render_buffer(self, buffer, offset=None):
		buffer.write(pack(self.unpack_as, self.value))
	
	#Printing and Formatting of tree
	def __str__(self):
		return str(self.value)
	
class TAG_Byte(_TAG_Numeric):
	id = TAG_BYTE
	def __init__(self, value=None, name=None, buffer=None):
		super(TAG_Byte, self).__init__(">b", 1, buffer, value, name)

class TAG_Short(_TAG_Numeric):
	id = TAG_SHORT
	def __init__(self, value=None, name=None, buffer=None):
		super(TAG_Short, self).__init__(">h", 2, buffer, value, name)

class TAG_Int(_TAG_Numeric):
	id = TAG_INT
	def __init__(self, value=None, name=None, buffer=None):
		super(TAG_Int, self).__init__(">i", 4, buffer, value, name)

class TAG_Long(_TAG_Numeric):
	id = TAG_LONG
	def __init__(self, value=None, name=None, buffer=None):
		super(TAG_Long, self).__init__(">q", 8, buffer, value, name)

class TAG_Float(_TAG_Numeric):
	id = TAG_FLOAT
	def __init__(self, value=None, name=None, buffer=None):
		super(TAG_Float, self).__init__(">f", 4, buffer, value, name)

class TAG_Double(_TAG_Numeric):
	id = TAG_DOUBLE
	def __init__(self, value=None, name=None, buffer=None):
		super(TAG_Double, self).__init__(">d", 8, buffer, value, name)

class TAG_Byte_Array(TAG):
	id = TAG_BYTE_ARRAY
	def __init__(self, value=None, name=None, buffer=None):
		super(TAG_Byte_Array, self).__init__(value, name)
		if self.value:
			self.length = TAG_Int(len(self.value))
		if buffer:
			self._parse_buffer(buffer)
	
	#Parsers and Generators	
	def _parse_buffer(self, buffer, offset=None):
		self.length = TAG_Int(buffer=buffer)
		self.value = buffer.read(self.length.value)
	
	def _render_buffer(self, buffer, offset=None):
		self.length._render_buffer(buffer, offset)
		buffer.write(self.value)
	
	#Accessors
	def __getitem__(self, key):
		if isinstance(key,int):
			return ord(self.value[key])
		else:
			raise TypeError("key needs to be integer")

	def __len__(self):
		return len(self.value)

	def __iter__(self):
		return self.value.__iter__()

	#Printing and Formatting of tree
	def __str__(self):
		return "[%i bytes]" % self.length.value
		
class TAG_String(TAG):
	id = TAG_STRING
	def __init__(self, value=None, name=None, buffer=None):
		super(TAG_String, self).__init__(value, name)
		if buffer:
			self._parse_buffer(buffer)
	
	#Parsers and Generators	
	def _parse_buffer(self, buffer, offset=None):
		self.length = TAG_Short(buffer=buffer)
		if self.length.value > 0:
			self.value = unicode(buffer.read(self.length.value), "utf-8")
		else: self.value = None
	
	def _render_buffer(self, buffer, offset=None):
		if self.value:
			save_val = self.value.encode("utf-8")
			self.length = TAG_Short(len(save_val))
			self.length._render_buffer(buffer, offset)
			if self.length > 0:
				buffer.write(save_val)
		else:
			self.length.value = 0
			self.length._render_buffer(buffer, offset)
			
	#Printing and Formatting of tree
	def __str__(self):
		if self.value:
			return self.value
		else:
			return ""
		
class TAG_List(TAG):
	id = TAG_LIST
	def __init__(self, name=None, type=None, buffer=None):
		super(TAG_List, self).__init__(name=name)
		if type: 
			self.tagID = TAG_Byte(value = type.id)
		else: self.tagID = None
		self.length = None
		self.tags = []
		if buffer:
			self._parse_buffer(buffer)
		if not self.tagID:
			raise AttributeError("Need to specify a tag type")
	
	#Parsers and Generators	
	def _parse_buffer(self, buffer, offset=None):
		self.tagID = TAG_Byte(buffer=buffer)
		self.length = TAG_Int(buffer=buffer)
		for x in range(self.length.value):
			self.tags.append(TAGLIST[self.tagID.value](buffer=buffer))
	
	def _render_buffer(self, buffer, offset=None):
		self.tagID._render_buffer(buffer, offset)
		self.length._render_buffer(buffer, offset)
		for tag in self.tags:
			tag._render_buffer(buffer, offset)
	
	#Accessors
	def __getitem__(self, key):
		return self.tags[key]

	def __setitem__(self, key, value):
		self.tags[key] = value

	def __delitem__(self, key):
		del self.tags[key]

	def __contains__(self, value):
		for i in self.tags:
			if i == value or i.name == value.name:
				return True
		return False

	def append(self, value):
		if not isinstance(value, TAGLIST[self.tagID.value]):
			raise TypeError("value needs to be type %s" % TAGLIST[self.tagID.value].__name__)
		self.tags.append(value)

	def insert(self, i, value):
		self.tags.insert(i, value)

	def __len__(self):
		return len(self.tags)

	def __iter__(self):
		return self.tags.__iter__()

	#Printing and Formatting of tree
	def __str__(self):
		return "%i entries of type %s" % (len(self.tags), TAGLIST[self.tagID.value].__name__)
	
	def pretty_tree(self, indent=0):
		output = [super(TAG_List,self).pretty_tree(indent)]
		if len(self.tags):
			output.append(("\t"*indent) + "{")
			output.extend([tag.pretty_tree(indent+1) for tag in self.tags])
			output.append(("\t"*indent) + "}")
		return '\n'.join(output)
			
class TAG_Compound(TAG):
	id = TAG_COMPOUND
	def __init__(self, buffer=None):
		super(TAG_Compound, self).__init__()
		self.tags = {}  # we're treating tagnames as unique...
		self.tagsort = []
		if buffer:
			self._parse_buffer(buffer)
	
	#Parsers and Generators
	def _parse_buffer(self, buffer, offset=None):
		while True:
			type = TAG_Byte(buffer=buffer)
			if type.value == TAG_END:
				#print "found tag_end"
				break
			else:
				name = TAG_String(buffer=buffer)
				try:
					#DEBUG print type, name
					tag = TAGLIST[type.value](buffer=buffer)
					tag.name = name
					self.tags[str(name)] = tag
					self.tagsort.append(str(name))
				except KeyError:
					raise ValueError("Unrecognised tag type")
	
	def _render_buffer(self, buffer, offset=None):
		for name in self.tagsort:
			tag = self.tags[name]
			TAG_Byte(tag.id)._render_buffer(buffer, offset)
			tag.name._render_buffer(buffer, offset)
			tag._render_buffer(buffer,offset)
		buffer.write('\x00') #write TAG_END
	
	#Accessors
	def __getitem__(self, key):
		if isinstance(key, int):
			return self.tags[self.tagsort[key]]
		elif isinstance(key, TAG_String):
			key = str(key)
		return self.tags[key]
					
	def __setitem__(self, key, value):
		if not isinstance(value, TAG):
			raise TypeError("Value needs to be a tag")
		if not isinstance(key, (str, TAG_String)):
			raise TypeError("key needs to be a string")
		if str(key) not in self.tagsort:
			self.tagsort.append(str(key))
		self.tags[str(key)] = value
		value.name = key

	def __delitem__(self, key):
		if not isinstance(key, (str, TAG_String)):
			raise TypeError("key needs to be a string")
		if str(key) not in self.tagsort:
			raise KeyError("key not found")
		self.tagsort.remove(str(key))
		del self.tags[str(key)]

	def __contains__(self, key):
		if not isinstance(key, (str, TAG_String)):
			raise TypeError("key type must be string")
		return str(key) in self.tagsort

	def __len__(self):
		return len(self.tags)

	def __iter__(self):
		return self.tagsort.__iter__()

	def append(self, value):
		if not isinstance(value, TAG):
			raise TypeError("Value needs to be a tag")
		if self.__contains__(value.name):
			raise KeyError("tag name already exists")
		self.tagsort.append(str(value.name))
		self.tags[str(value.name)] = value

	def insert(self, i, value):
		if not isinstance(value, TAG):
			raise TypeError("Value needs to be a tag")
		if self.__contains__(value.name):
			raise KeyError("tag name already exists")
		self.tagsort.insert(i, str(value.name))
		self.tags[str(value.name)] = value

	def keys(self):
		return self.tagsort
	
	#Printing and Formatting of tree
	def __str__(self):
		return '%i Entries' % len(self.tags)
		
	def pretty_tree(self, indent=0):
		output = [super(TAG_Compound,self).pretty_tree(indent)]
		if len(self.tags):
			output.append(("\t"*indent) + "{")
			output.extend([self.tags[tag].pretty_tree(indent+1) for tag in self.tagsort])
			output.append(("\t"*indent) + "}")
		return '\n'.join(output)
		

TAGLIST = {TAG_BYTE:TAG_Byte, TAG_SHORT:TAG_Short, TAG_INT:TAG_Int, TAG_LONG:TAG_Long, TAG_FLOAT:TAG_Float, TAG_DOUBLE:TAG_Double, TAG_BYTE_ARRAY:TAG_Byte_Array, TAG_STRING:TAG_String, TAG_LIST:TAG_List, TAG_COMPOUND:TAG_Compound}		

class NBTFile(TAG_Compound):
	"""Represents an NBT file object"""
	
	def __init__(self, filename=None, mode=None, buffer=None, name=None):
		super(NBTFile,self).__init__()
		self.__class__.__name__ = "TAG_Compound"
		self.type = TAG_Byte(self.id)
		if filename:
			self.file = GzipFile(filename, mode)
			self.parse_file(self.file)
		elif buffer:
			self.parse_file(StringIO(buffer))
		elif name:
			if isinstance(name, str):
				self.name = TAG_String(name)
			elif isinstance(name, TAG_String):
				self.name = name
			else:
				raise TypeError("Need to specify either a string or TAG_String")
	
	def parse_file(self, file=None):
		if not file:
			file = self.file
		if file:
			self.type = TAG_Byte(buffer=file)
			if self.type.value == self.id:
				name = TAG_String(buffer=file)
				self._parse_buffer(file)
				self.name = name
				self.file.close()
			else:
				raise ValueError("First record is not a Compound Tag")

	def write_file(self, filename=None, file=None):
		if file:
			self.file = file
		elif filename:
			self.file = GzipFile(filename, "wb")
		elif not self.file:
			raise AttributeError("Need to specify either a filename or a file")
		#Render tree to file
		self.type._render_buffer(self.file)
		self.name._render_buffer(self.file)
		self._render_buffer(self.file)
	
