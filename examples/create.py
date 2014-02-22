import ndef


smart_poster_message = ndef.new_smart_poster('Github', 'http://github.com/')
smart_poster_raw_ndef = smart_poster_message.to_buffer()
print 'smart poster ndef:', smart_poster_raw_ndef.encode('hex')

text_record = (ndef.TNF_WELL_KNOWN, ndef.RTD_TEXT, 'id', 'hello world')
text_message = ndef.new_message(text_record)
text_raw_ndef = text_message.to_buffer()
print 'text ndef:', text_raw_ndef.encode('hex')
