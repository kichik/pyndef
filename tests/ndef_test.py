import sys
import unittest

import six

from ndef.ndef import BufferReader, InvalidNdef, NdefMessage, InvalidNdefMessage, InvalidNdefRecord, new_message, \
    TNF_EMPTY, TNF_WELL_KNOWN, RTD_TEXT, BufferWriter, new_smart_poster, _url_ndef_abbrv


# TODO chunked
# TODO long records

def decode_hex(x):
    if sys.version_info.major == 2:
        return x.decode('hex')
    else:
        return bytes.fromhex(x)


class TestNdefClass(unittest.TestCase):
    def test_reader(self):
        b = BufferReader(decode_hex('0123456789abcdef'))

        self.assertEqual(b.read_8(), 1)
        self.assertEqual(b.read_16(), 0x4523)
        self.assertEqual(b.read_32(), 0xcdab8967)
        self.assertEqual(b.read(1), decode_hex('ef'))

        with self.assertRaises(InvalidNdef):
            b.read_32()

        with self.assertRaises(InvalidNdef):
            b.read(1)

        b.read(0)

    def test_writer(self):
        bw = BufferWriter()
        bw.write_8(0x4f)
        bw.write_16(0x1234)
        bw.write_32(0x12345678)
        bw.write_str('test')
        b = bw.get()

        self.assertEqual(b, decode_hex('4f341278563412') + six.b('test'))

        with self.assertRaises(InvalidNdef):
            bw.write_8(1000)

    def _test_valid_ndef(self, data):
        NdefMessage(decode_hex(data))

    def _test_invalid_ndef(self, data):
        with self.assertRaises(InvalidNdef):
            NdefMessage(decode_hex(data))

    def _test_invalid_ndef_message(self, data):
        with self.assertRaises(InvalidNdefMessage):
            NdefMessage(decode_hex(data))

    def _test_invalid_ndef_record(self, data):
        with self.assertRaises(InvalidNdefRecord):
            NdefMessage(decode_hex(data))

    def test_verification(self):
        # empty message
        self._test_invalid_ndef('')
        # 1 short record
        self._test_valid_ndef('d901050155610123456761')
        # 1 long record
        self._test_valid_ndef('c901050000000155610123456761')
        # 1 truncated record
        self._test_invalid_ndef('d90105015561')
        # 1 short record, 1 long record
        self._test_valid_ndef('99010501556101234567614901050000000155610123456761')
        # 1 long record, 1 short record
        self._test_valid_ndef('89010500000001556101234567615901050155610123456761')
        # 2 begin/end records
        self._test_invalid_ndef_message('d901050155610123456761d901050155610123456761')
        # mid-message end
        self._test_invalid_ndef_message('b9010101556100760001ff560001ff')
        # no end record
        self._test_invalid_ndef_message('9901050155610123456761')
        # no begin record
        self._test_invalid_ndef_message('5901050155610123456761')
        # 3 record chunked payload
        self._test_valid_ndef('b9010101556100360001ff560001ff')
        # unfinished chunked payload
        self._test_invalid_ndef_message('b9010101556100360001ff')
        # middle chunk not unchanged
        self._test_invalid_ndef_message('b9010101556100310001ff560001ff')
        # middle chunk with id
        self._test_invalid_ndef_record('b90101015561003e000101eeff560001ff')
        # middle chunk with type
        self._test_invalid_ndef_record('b9010101556100360101eeff560001ff')
        # end chunk not unchanged
        self._test_invalid_ndef_message('b9010101556100360001ff510001ff')
        # first record unchanged
        self._test_invalid_ndef_message('d60000')
        # empty record
        self._test_valid_ndef('d00000')
        # empty record with payload
        self._test_invalid_ndef_record('d00001ff')
        # empty record with id
        self._test_invalid_ndef_record('d8000001ff')
        # empty record with type
        self._test_invalid_ndef_record('d00100ff')
        # unknown record
        self._test_valid_ndef('d50000')
        # unknown record with type
        self._test_invalid_ndef_record('d50100ff')
        # reserved record
        self._test_invalid_ndef_record('d70000')
        # ANDROID: non-empty-type first record
        self._test_valid_ndef('d10100ff')
        # ANDROID: empty-type first record
        self._test_invalid_ndef_message('d10000')

    def test_real_life(self):
        # text
        self._test_valid_ndef('D1010F5402656E48656C6C6F20776F726C6421')
        # utf-8 text
        self._test_valid_ndef('D101185402656EC2A3E282AC24C2A5C2A4C2A1C2BFC2A7237C200D0A')
        # smart poster internal
        self._test_valid_ndef(
            '9101175500687474703a2f2f7777772e676f6f676c652e636f6d2f110301616374005101095402656e476f6f676c65')
        # smart poster
        self._test_valid_ndef(
            'd1023353709101195500687474703a2f2f7777772e66616365626f6' +
            'f6b2e636f6d2f1103016163740051010b5402656e46616365626f6f6b')

    def test_invalid_well_known_records(self):
        # RTD_URI with no valid prefix
        self._test_invalid_ndef_record('d1011655687474703a2f2f7777772e6d6b746167732e636f6d2f')
        # RTD_URI with another invalid prefix (0xff)
        self._test_invalid_ndef_record('d1011655ff7474703a2f2f7777772e6d6b746167732e636f6d2f')
        # RTD_URI with invalid utf-8
        self._test_invalid_ndef_record('d1011655687474703a2f2f8822772e6d6b746167732e636f6d2f')
        # RTD_TEXT with no status byte or language
        self._test_invalid_ndef_record('d101045474657874')
        # RTD_TEXT with invalid utf-8
        self._test_invalid_ndef_record('d10102548822')
        # RTD_URI with invalid utf-8 inside RTD_SMART_POSTER
        self._test_invalid_ndef_record(
            'd10228537091010e550188226365626f6f6b2e636f6d2f1103016163740051010b5402656e46616365626f6f6b')

    def _test_valid_ndef_write(self, expected, *records):
        msg = new_message(*records)
        raw = msg.to_buffer()
        self.assertEqual(decode_hex(expected), raw)
        msg2 = NdefMessage(raw)
        raw2 = msg2.to_buffer()
        self.assertEqual(decode_hex(expected), raw2)

    def _test_invalid_ndef_write(self, *records):
        with self.assertRaises(InvalidNdef):
            new_message(*records)

    def test_writing(self):
        # empty record
        self._test_valid_ndef_write('d00000', (TNF_EMPTY, six.b(''), six.b(''), six.b('')))
        # two empty records
        self._test_valid_ndef_write('900000500000',
                                    (TNF_EMPTY, six.b(''), six.b(''), six.b('')),
                                    (TNF_EMPTY, six.b(''), six.b(''), six.b('')))
        # not really empty record
        self._test_invalid_ndef_write((TNF_EMPTY, six.b('a'), six.b(''), six.b('')))
        self._test_invalid_ndef_write((TNF_EMPTY, six.b(''), six.b('a'), six.b('')))
        self._test_invalid_ndef_write((TNF_EMPTY, six.b(''), six.b(''), six.b('a')))
        # invalid inputs
        self._test_invalid_ndef_write((TNF_EMPTY,))
        self._test_invalid_ndef_write((TNF_EMPTY, six.b(''), six.b(''), six.b(''), six.b('')))
        # non-empty id
        self._test_valid_ndef_write('d90108055468656c6c6f02656e776f726c64',
                                    (TNF_WELL_KNOWN, RTD_TEXT, six.b('hello'), six.b('\x02enworld')))

    def test_writing_smart_poster(self):
        msg = new_smart_poster('Facebook', 'http://www.facebook.com/')
        raw_msg = msg.to_buffer()
        self.assertEqual(
            decode_hex('d10228537091010e550166616365626f6f6b2e636f6d2f1103016163740051010b5402656e46616365626f6f6b'),
            raw_msg)

        new_smart_poster('Facebook' * 400, 'x' * 400)

    def test_url_ndef_abbrv(self):
        self.assertEqual(_url_ndef_abbrv('http://test.com'), six.b('\x03test.com'))
        self.assertEqual(_url_ndef_abbrv('https://test.com'), six.b('\x04test.com'))
        self.assertEqual(_url_ndef_abbrv('myproto://test.com'), six.b('\x00myproto://test.com'))
