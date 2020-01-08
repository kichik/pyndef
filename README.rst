#################################################
Python Module for NFC Data Exchange Format (NDEF)
#################################################

Release v0.2 -- January 7th, 2020

The **ndef** modules provides methods for encoding and decoding messages and records in the NDEF format according to NFC
Forum technical specification. Its main purpose is to provide comprehensive verification of raw NDEF messages. It can be
used to verify messages before writing them to an actual tag.

Available on PyPI_.

.. _PyPI: https://pypi.python.org/pypi/ndef/

.. image:: https://travis-ci.org/kichik/pyndef.svg?branch=master
   :target: https://travis-ci.org/kichik/pyndef

.. image:: https://badge.fury.io/py/pyndef.svg
    :target: https://badge.fury.io/py/ndef


Usage
-----

Valid Message
~~~~~~~~~~~~~

  >>> import ndef
  >>> message_data = 'D1010F5402656E48656C6C6F20776F726C6421'.decode('hex')
  >>> message = ndef.NdefMessage(message_data)
  >>> record = message.records[0]
  >>> record.tnf
  1
  >>> record.type
  'T'
  >>> record.id
  >>> record.payload
  '\x02enHello world!'
  >>>

Invalid Message
~~~~~~~~~~~~~~~

  >>> import ndef
  >>> message_data = '9901050155610123456761'.decode('hex')
  >>> message = ndef.NdefMessage(message_data)
  Traceback (most recent call last):
    File "<stdin>", line 1, in <module>
    File "ndef\ndef.py", line 274, in __init__
      self.verify()
    File "ndef\ndef.py", line 278, in verify
      self._verify_begin_end()
    File "ndef\ndef.py", line 296, in _verify_begin_end
      raise InvalidNdefMessage("last record's ME flag is off")
  ndef.ndef.InvalidNdefMessage: last record's ME flag is off
  >>>

Create Message
~~~~~~~~~~~~~~

  >>> import ndef
  >>> text_record = (ndef.TNF_WELL_KNOWN, ndef.RTD_TEXT, 'id', 'hello world')
  >>> text_message = ndef.new_message(text_record)
  >>> text_raw_ndef = text_message.to_buffer()
  >>> text_raw_ndef.encode('hex')
  'd9010b0254696468656c6c6f20776f726c64'
  >>>

Alternatives
------------

- nfcpy_: full implementation of spec including actual communication code
- `Python NDEF library and tools`_: aimed at security research
- `pynfc`_: pythonic interface for the libnfc library

.. _nfcpy: http://nfcpy.readthedocs.org/
.. _Python NDEF library and tools: http://mulliner.org/nfc/feed/collins_nfcndef_python_stuff.tgz
.. _pynfc: https://code.google.com/p/pynfc/

License
-------

::

  Copyright (c) 2014 Amir Szekely
  
  This software is provided 'as-is', without any express or implied
  warranty. In no event will the authors be held liable for any damages
  arising from the use of this software.
  
  Permission is granted to anyone to use this software for any purpose,
  including commercial applications, and to alter it and redistribute it
  freely, subject to the following restrictions:
  
     1. The origin of this software must not be misrepresented; you must not
     claim that you wrote the original software. If you use this software
     in a product, an acknowledgment in the product documentation would be
     appreciated but is not required.
  
     2. Altered source versions must be plainly marked as such, and must not be
     misrepresented as being the original software.
  
     3. This notice may not be removed or altered from any source
     distribution.
