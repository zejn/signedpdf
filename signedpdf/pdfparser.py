from collections import namedtuple, OrderedDict

XrefItem = namedtuple('XrefItem', ['position', 'generation'])

# taken from chapter 7.2.2 Character set
delimiter = b"()<>[]{}/%"
whitespace_chars = b"\x00\x09\x0a\x0c\x0d\x20"


def encode_name(name):
    encoded = name.encode('utf-8')
    final = []
    special = delimiter + whitespace_chars
    for char in encoded:
        if char in special:
            final.append('#' + ('%x' % ord(char)))
        else:
            final.append(char)
    return b''.join(final)


def encode_item(obj):
    if isinstance(obj, int):
        return str(obj).encode('utf-8')
    else:
        raise ValueError("invalid object passed into encode_item")


def escape_string(s):
    return s


class IndirectRef(object):
    def __init__(self, ref):
        self.ref = ref

class Ref(object):
    def __init__(self, obj, ref_id, generation=0):
        self.obj = obj
        self.ref_id = ref_id
        self.generation = generation

    def as_indirect(self):
        # Chapter 7.3.10 inirect objects
        # return reference
        return IndirectRef(self)

    def as_data(self):
        # return as object with
        # FIXME
        pass

    def __repr__(self):
        return 'ref_id: %d generation: %d' % (self.ref_id, self.generation)


class XRef(object):
    def __init__(self):
        self.xref = OrderedDict()

    def ref(self, obj):
        if obj in self.xref:
            return self.xref[obj]
        self.xref[obj] = len(self.xref) + 1
        return obj


class PDFDict(object):
    def __init__(self, **kwargs):
        self.values = kwargs

    def as_data(self):
        b = [b'<<']
        for k in self.values:
            b.append(b' /')
            b.append(encode_name(k))
            b.append(b' ')
            b.append(encode_item(self.values[k]))

        b.append(b'>>')
        return b''.join(b)

    def __getitem__(self, key):
        return self.values[key]

    def __setitem__(self, key, value):
        self.values[key] = value


class Name(object):
    def __init__(self, val):
        self.value = val

class Root(PDFDict):
    # chapter 7.7.2 Document Catalog
    def __init__(self, **kwargs):
        super(Root, self).__init__()
        # Mandatory keys are "Type" (set to "Catalog")
        # and "Pages" (indirect ref)
        self['Type'] = Name('Catalog')
        # FIXME add Pages


class Pages(PDFDict):
    # Chapter 7.7.3 Page tree
    def __init__(self, pdf, **kwargs):
        super(Pages, self).__init__()
        # Mandatory keys are:
        # - "Type", string "Pages"
        # - "Parent", dict
        # - "Kids"
        # - "Count"
        self.pdf = pdf
        self.pdf.root['Pages'] = self.pdf.make_ref(self).as_indirect()
        self['Type'] = Name('Pages')
        self['Kids'] = []
        self['Count'] = 0
        self['MediaBox'] = [0, 0, 300, 144]

    def add_page(self, page):
        page_ref = self.pdf.make_ref(page)
        self['Kids'].append(IndirectRef(page_ref))
        self['Count'] = len(self['Kids'])


class Page(PDFDict):
    def __init__(self):
        super(Page, self).__init__()
        self['Type'] = Name('Page')



class PDF(object):
    newline = b'\n'

    def __init__(self):
        self.xref = OrderedDict()
        self.trailer_dict = PDFDict()
        self.root = Root()
        self.pages = Pages(self)

    def write(self, fd):
        """
        Use this function to write the PDF.

        :param fd: open file handle, where the PDF is to be written
        """
        self.write_header(fd)
        self.write_objects(fd)
        self.write_xref(fd)
        self.write_trailer(fd)

    def make_ref(self, obj):
        try:
            ref_obj = self.xref[obj]
        except KeyError:
            ref_obj = Ref(obj, len(self.xref) + 1)
            self.xref[obj] = ref_obj
        return ref_obj

    def write_header(self, fd):
        "Write PDF header"
        # write PDF header with version
        fd.write(b"%PDF-1.1 " + self.newline)
        # write 6 high-bit bytes, for heuristics to detect this file binary
        fd.write(b"%\xc2\xa5\xc2\xb1\xc3\xab" + self.newline)

    # done!

    def write_obj(self, fd, obj):
        # 7.3.7 Dictionary objects
        if isinstance(obj, (dict, PDFDict)):
            if isinstance(obj, PDFDict):
                real_obj = obj.values
            else:
                real_obj = obj
            fd.write(b'<<')
            for k, v in real_obj.items():
                fd.write(b'/')
                fd.write(k.encode('utf-8'))
                fd.write(b' ')
                self.write_obj(fd, v)
            fd.write(b' >> \n')
        elif isinstance(obj, int):
            fd.write(str(obj).encode('utf-8'))
        elif obj is True:
            fd.write(b' true ')
        elif obj is False:
            fd.write(b' false ')
        # 7.3.4.2 Literal strings
        elif isinstance(obj, str):
            fd.write(b'(')
            fd.write(obj.encode('utf-8'))
            fd.write(b')')
        # 7.3.5 Name objects
        elif isinstance(obj, Name):
            fd.write(b'/')
            fd.write(obj.value.encode('utf-8'))
            fd.write(b' ')
        elif isinstance(obj, Ref):
            obj.position = fd.tell()
            fd.write(b'%d %d obj\n' % (obj.ref_id, obj.generation))
            self.write_obj(fd, obj.obj)
            fd.write(b'\nendobj\n')
        elif isinstance(obj, IndirectRef):
            fd.write(b'%d %d R ' % (obj.ref.ref_id, obj.ref.generation))
        # 7.3.6 Array objects
        elif isinstance(obj, list):
            fd.write(b'[')
            for elem in obj:
                self.write_obj(fd, elem)
                fd.write(b' ')
            fd.write(b']')
        else:
            raise ValueError("invalid object: %r" % obj)

    def write_objects(self, fd):
        # XXX FIXME this still needs to be implemented
        root_ref = self.make_ref(self.root)
        self.trailer_dict.values['Root'] = root_ref.as_indirect()
        self.write_obj(fd, root_ref)
        pages_ref = self.make_ref(self.pages)

        self.write_obj(fd, pages_ref)

        for obj in self.xref.values():
            if not hasattr(obj, 'position'):
                self.write_obj(fd, obj)

    def write_xref(self, fd):
        "Write the PDF object index"
        self.last_xref_position = fd.tell()
        # indicate start of xref
        fd.write(b'xref' + self.newline)

        num_all = len(self.xref) + 1  # also count first entry
        # also set Size in trailer dictionary
        self.trailer_dict['Size'] = num_all
        first = 0
        # write subsection start and element count
        fd.write("{} {}".format(first, num_all).encode('utf-8'))
        fd.write(self.newline)
        # first entry is special and has object id 0 and generation 65535
        first_entry = XrefItem(0, 65535)
        # format according to chapter 7.5.4 of PDF spec
        itemfmt = '{:0=10} {:0=5} n '
        for item in [first_entry] + self.xref.values():
            itemline = itemfmt.format(item.position, item.generation)
            itemline = itemline.encode('utf-8') + self.newline
            # each xref entry must be 20 bytes long
            assert len(itemline) == 20, "xref entry is not 20 bytes long"
            fd.write(itemline)

    def write_trailer(self, fd):
        "Write the PDF trailer"
        # Chapter 7.5.5 File trailer
        # start trailer
        fd.write('trailer' + self.newline)
        # write trailer dict
        # FIXME
        self.write_obj(fd, self.trailer_dict)
        # write the location of xref
        fd.write(b'startxref' + self.newline)
        fd.write('{}'.format(self.last_xref_position).encode('utf-8') + self.newline)
        # end of file
        fd.write(b'%%EOF')
