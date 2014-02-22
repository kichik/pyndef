import ndef


print 'parsing valid ndef'

message_data = 'D1010F5402656E48656C6C6F20776F726C6421'.decode('hex')
message = ndef.NdefMessage(message_data)
record = message.records[0]

print '  tnf:    ', record.tnf
print '  type:   ', record.type
print '  id:     ', record.id
print '  payload:', record.payload

print ''
print 'parsing invalid ndef'

message_data = '9901050155610123456761'.decode('hex')
try:
    message = ndef.NdefMessage(message_data)
    assert False, 'this should never happen'
except ndef.InvalidNdef, e:
    print '  %s: %s' % (e.__class__.__name__, e.message)
