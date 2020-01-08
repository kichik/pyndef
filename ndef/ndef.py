# based on NFC Data Exchange Format (NDEF) Technical Specification from nfc-forum.org
# and http://androidxref.com/source/xref/external/libnfc-nxp/src/phFriNfc_NdefRecord.c
#   line 87 - phFriNfc_NdefRecord_GetRecords()

import functools
import struct

import six


class InvalidNdef(Exception):
    pass


class InvalidNdefMessage(InvalidNdef):
    pass


class InvalidNdefRecord(InvalidNdef):
    pass


FLAGS_MB = 0x80
FLAGS_ME = 0x40
FLAGS_CHUNKED = 0x20
FLAGS_SHORT = 0x10
FLAGS_ID = 0x08
FLAGS_TNF_MASK = 0x07

TNF_EMPTY = 0x00
TNF_WELL_KNOWN = 0x01
TNF_MEDIA = 0x02
TNF_URI = 0x03
TNF_EXTERNAL = 0x04
TNF_UNKNOWN = 0x05
TNF_UNCHANGED = 0x06
TNF_RESERVED = 0x07

RTD_TEXT = six.b('T')
RTD_URI = six.b('U')
RTD_SMART_POSTER = six.b('Sp')

RTD_URI_ABBRIV_NUM = 35

SIZE2STRUCT = {
    8: '<B',
    16: '<H',
    32: '<L',
}


class BufferReader(object):
    def __init__(self, buffer):
        self.buffer = buffer
        self.offset = 0

        for size in SIZE2STRUCT:
            setattr(self, 'read_%d' % size, functools.partial(self._read, size))

    def _read(self, size):
        try:
            res = struct.unpack_from(SIZE2STRUCT[size], self.buffer, self.offset)
        except struct.error:
            raise InvalidNdef('not enough bytes')
        self.offset += int(size / 8)
        return res[0]

    def read(self, size):
        if self.offset + size > len(self.buffer):
            raise InvalidNdef('not enough bytes [offset=%u, len=%u, need=%u]' % (self.offset, len(self.buffer), size))
        res = self.buffer[self.offset:self.offset + size]
        self.offset += size
        return res

    def eob(self):
        return len(self.buffer) - self.offset == 0


class BufferWriter(object):
    def __init__(self):
        self.buffer = six.b('')

        for size in SIZE2STRUCT:
            setattr(self, 'write_%d' % size, functools.partial(self._write, size))

    def _write(self, size, data):
        try:
            self.buffer += struct.pack(SIZE2STRUCT[size], data)
        except struct.error:
            raise InvalidNdef('bad number')

    def write_str(self, data):
        self.buffer += data.encode('utf-8')

    def write_bytes(self, data):
        self.buffer += data

    def get(self):
        return self.buffer


class NdefRecordFlags(object):
    def __init__(self):
        self.message_begin = False
        self.message_end = False
        self.chunked = False
        self.short = False
        self.id = False


class NdefRecord(object):
    def __init__(self, reader=None):
        self.flags = NdefRecordFlags()
        self.tnf = TNF_EMPTY
        self.type_len = 0
        self.type = None
        self.id_len = 0
        self.id = None
        self.payload_len = 0
        self.payload = None

        if reader is None:
            return

        flags_raw = reader.read_8()
        if flags_raw & FLAGS_MB:
            self.flags.message_begin = True
        if flags_raw & FLAGS_ME:
            self.flags.message_end = True
        if flags_raw & FLAGS_CHUNKED:
            self.flags.chunked = True
        if flags_raw & FLAGS_SHORT:
            self.flags.short = True
        if flags_raw & FLAGS_ID:
            self.flags.id = True

        self.tnf = flags_raw & FLAGS_TNF_MASK

        self.type_len = reader.read_8()

        if self.flags.short:
            self.payload_len = reader.read_8()
        else:
            self.payload_len = reader.read_32()

        if self.flags.id:
            self.id_len = reader.read_8()
        else:
            self.id_len = 0

        self.type = reader.read(self.type_len)

        if self.flags.id:
            self.id = reader.read(self.id_len)
        else:
            self.id = None

        self.payload = reader.read(self.payload_len)

        self.verify()

    def verify(self):
        if self.tnf == TNF_EMPTY:
            if self.type_len or self.id_len or self.payload_len:
                raise InvalidNdefRecord("TNF is set to 'empty' but record not empty")

        if self.tnf == TNF_UNKNOWN:
            if self.type_len:
                raise InvalidNdefRecord("TNF is set to 'unknown' but type not empty")

        if self.tnf == TNF_UNCHANGED:
            if self.type_len:
                raise InvalidNdefRecord("TNF is set to 'unchanged' but type not empty")
            if self.flags.id:
                raise InvalidNdefRecord("TNF is set to 'unchanged' but id flag is on")

        if self.tnf == TNF_RESERVED:
            raise InvalidNdefRecord("TNF is set to 'reserved' (0x07)")

        if self.tnf == TNF_WELL_KNOWN:
            if self.type == RTD_TEXT:
                if len(self.payload) == 0:
                    raise InvalidNdefRecord('RTD_TEXT payload missing status byte')

                encoding = 'utf-8'
                if six.byte2int(self.payload) & 0x80:
                    encoding = 'utf-16'

                language_len = six.byte2int(self.payload) & 0x1f
                if self.payload_len < 1 + language_len:
                    raise InvalidNdefRecord('RTD_TEXT contains invalid language code length')

                try:
                    self.payload[1:1 + language_len].decode('us-ascii')
                except UnicodeDecodeError:
                    raise InvalidNdefRecord('RTD_TEXT contains language code with invalid encoding')

                try:
                    self.payload[language_len + 1:].decode(encoding)
                except UnicodeDecodeError:
                    raise InvalidNdefRecord('RTD_TEXT payload failed to decode as ' + encoding)

            elif self.type == RTD_URI:
                if len(self.payload) == 0:
                    raise InvalidNdefRecord('RTD_URI payload missing status byte')

                if six.byte2int(self.payload) > RTD_URI_ABBRIV_NUM:
                    raise InvalidNdefRecord('RTD_URI payload starts with an invalid URI identifier code')

                try:
                    self.payload[1:].decode('utf-8')
                except UnicodeDecodeError:
                    raise InvalidNdefRecord('RTD_URI payload failed to decode as utf-8')

            elif self.type == RTD_SMART_POSTER:
                # parse internal message to verify it contains no errors
                NdefMessage(self.payload)

                # TODO verify all other well known types

    def set_type(self, new_type):
        self.type = new_type
        self.type_len = len(self.type)

    def set_id(self, new_id):
        self.id = new_id
        self.id_len = len(self.id)
        self.flags.id = self.id_len > 0

    def set_payload(self, new_payload):
        self.payload = new_payload
        self.payload_len = len(self.payload)
        self.flags.short = self.payload_len < 256

    def to_buffer(self):
        w = BufferWriter()
        w.write_8(self._raw_flags() | self.tnf)
        w.write_8(self.type_len)
        if self.flags.short:
            w.write_8(self.payload_len)
        else:
            w.write_32(self.payload_len)
        if self.flags.id:
            w.write_8(self.id_len)
        w.write_bytes(self.type)
        if self.flags.id:
            w.write_bytes(self.id)
        w.write_bytes(self.payload)
        return w.get()

    def _raw_flags(self):
        raw = 0
        if self.flags.chunked:
            raw |= FLAGS_CHUNKED
        if self.flags.id:
            raw |= FLAGS_ID
        if self.flags.message_begin:
            raw |= FLAGS_MB
        if self.flags.message_end:
            raw |= FLAGS_ME
        if self.flags.short:
            raw |= FLAGS_SHORT
        return raw


class NdefMessage(object):
    def __init__(self, data=None):
        self.records = []

        if data is None:
            return

        reader = BufferReader(data)
        while not reader.eob():
            self.records.append(NdefRecord(reader))
        if not self.records:
            raise InvalidNdef("empty NDEF message")

        self.verify()

    def verify(self):
        self._verify_records()
        self._verify_begin_end()
        self._verify_chunks()
        self._verify_android_specific()

    def to_buffer(self):
        return six.b('').join(r.to_buffer() for r in self.records)

    def _verify_records(self):
        for r in self.records:
            r.verify()

    def _verify_begin_end(self):
        if not self.records[0].flags.message_begin:
            raise InvalidNdefMessage("first record's MB flag is off")
        for r in self.records[1:]:
            if r.flags.message_begin:
                raise InvalidNdefMessage("MB flag is on for non-first record")
        if not self.records[-1].flags.message_end:
            raise InvalidNdefMessage("last record's ME flag is off")
        for r in self.records[:-1]:
            if r.flags.message_end:
                raise InvalidNdefMessage("ME flag is on for non-last record")

    def _verify_chunks(self):
        chunked = False
        for r in self.records:
            if chunked:
                if r.tnf != TNF_UNCHANGED:
                    raise InvalidNdefMessage("record chunk type is not 'unchanged'")
            elif r.tnf == TNF_UNCHANGED:
                raise InvalidNdefMessage("non-chunked record type is 'unchanged'")

            chunked = r.flags.chunked

        if self.records[-1].flags.chunked:
            raise InvalidNdefMessage("last record still chunked")

    def _verify_android_specific(self):
        if self.records[0].tnf != TNF_UNKNOWN and self.records[0].tnf != TNF_EMPTY:
            if not self.records[0].type_len:
                raise InvalidNdefMessage("first record has no type, but is also not empty or unknown")


def new_message(*record_defs):
    records = []
    for record_def in record_defs:
        if len(record_def) != 4:
            raise InvalidNdefRecord('invalid record definition - wrong length [%d but should be 4]' % len(record_def))
        record = NdefRecord()
        record.tnf = record_def[0]
        record.set_type(record_def[1])
        record.set_id(record_def[2])
        record.set_payload(record_def[3])
        records.append(record)

    records[0].flags.message_begin = True
    records[-1].flags.message_end = True

    message = NdefMessage()
    message.records = records
    message.verify()

    return message


def _url_ndef_abbrv(url):
    abbrv_table = """http://www.
    https://www.
    http://
    https://
    tel:
    mailto:
    ftp://anonymous:anonymous@
    ftp://ftp.
    ftps://
    sftp://
    smb://
    nfs://
    ftp://
    dav://
    news:
    telnet://
    imap:
    rtsp://
    urn:
    pop:
    sip:
    sips:
    tftp:
    btspp://
    btl2cap://
    btgoep://
    tcpobex://
    irdaobex://
    file://
    urn:epc:id:
    urn:epc:tag:
    urn:epc:pat:
    urn:epc:raw:
    urn:epc:
    urn:nfc:""".split()

    assert len(abbrv_table) == RTD_URI_ABBRIV_NUM

    for i, abbr in enumerate(abbrv_table):
        if url.startswith(abbr):
            return six.int2byte(i + 1) + url[len(abbr):].encode('utf-8')

    return six.int2byte(0) + url.encode('utf-8')


def new_smart_poster(title, url):
    records = [
        (TNF_WELL_KNOWN, RTD_URI, six.b(''), _url_ndef_abbrv(url)),
        (TNF_WELL_KNOWN, six.b('act'), six.b(''), six.b('\x00')),
    ]
    if title:
        records.append((TNF_WELL_KNOWN, RTD_TEXT, six.b(''), six.b('\x02en') + title.encode('utf-8')))
    internal_message = new_message(*records)
    raw_internal = internal_message.to_buffer()
    return new_message((TNF_WELL_KNOWN, RTD_SMART_POSTER, six.b(''), raw_internal))
