#!/usr/bin/python

import datetime
import sys

USE_TRUNK_OUT_FROM_110 = False

def get_data():
  while True:
    data = sys.stdin.read( 3 )
    if len(data) != 3:
      return None
    c = ord(data[0])
    if c != 200:
      if c == 210:
        c = 16 # data change record
      elif c == 211:
        c = 16 # lost info record
      elif c == 212:
        c = 12 # restart record
      else:
        return None # unkonwn record type
      sys.stdin.read( c - 3 )
      continue
    else:
      c = ord(data[1]) * 0x100 + ord(data[2])
    if c < 3:
      return None # wrong record size
    if c > 1024:
      return None # record is too long
    else:
      return data + sys.stdin.read( c - 3 )

def get_bcd( data, begin, end ):
  ret = ""
  i = begin
  while i < end:
    current = ord(data[i/2])
    if i % 2:
      current &= 0x0F
    else:
      current = (current & 0xF0) / 0x10
    if current < 0x0A:
      ret += chr( ord('0') + current )
    elif current == 0x0A:
      ret += '0'
    elif current == 0x0B:
      ret += '*'
    elif current == 0X0C:
      ret += '#'
    else:
      ret += ' '
    i += 1
  return ret

class Record:
  def __init__ ( self, data ):
    self.type = ord(data[0])
    self.length = 0 # 1, 2
    self.sequence_id = 0 # 3,4,5,6
    self.process_id = 0 # 7,8,9,10
    self.process_id = self.process_id * (2**8) + ord(data[7])
    self.process_id = self.process_id * (2**8) + ord(data[8])
    self.process_id = self.process_id * (2**8) + ord(data[9])
    self.process_id = self.process_id * (2**8) + ord(data[10])
    self.flags1 = ord(data[11])
    self.flags9 = ord(data[12])
    self.flags17 = ord(data[13])
    self.sequence_info = ord(data[14])
    self.abonent_len = ord(data[15])
    self.abonent_num_offset = 16

def parse_data( data, cache ):
  ret = {}
  r = Record( data )
  print >>sys.stderr, "Flags %02x%02x%02x" % ( r.flags1, r.flags9, r.flags17 )
  code_l = (r.abonent_len & 0xE0) / 0x20
  num_l = r.abonent_len & 0x1F;
  if r.flags1 & 0x01 == 0:
    print >> sys.stderr, "Not a call record, ignored"
    return []
  elif r.flags1 & 0x08:
    print >> sys.stderr, "Successed call found"
  else:
    print >> sys.stderr, "Failed call found (F4 = 0)"
  seq = r.sequence_info & 0xF0 / 0x10
  if seq == 1:
    print >> sys.stderr, "Single record found"
  elif seq == 2:
    print >> sys.stderr, "First record in sequence found"
  elif seq == 3:
    print >> sys.stderr, "Intermediate record in sequence found"
  elif seq == 4:
    print >> sys.stderr, "The last record in sequence found"
  print >> sys.stderr, "Call Id = %s" % r.process_id
  print >> sys.stderr, "Charge Status = %s" % (r.sequence_info & 0x0F, )
  ret['uniqueid'] = str(r.process_id)
  ret['numfrom'] = get_bcd( data[r.abonent_num_offset:], 0, code_l + num_l )
  p = r.abonent_num_offset + (code_l + num_l + 1) / 2
  if ord(data[p]) == 100:
    p += 1
    num_l = ord(data[p])
    p += 1
    ret['numto'] = get_bcd( data[p:], 0, num_l )
  if ord(data[p]) == 101:
    print >> sys.stderr, "Forwarded calls not supported, processing as common call"
    p += 2
    num_l = ord(data[p])
    p += (num_l + 1) / 2
  p += (num_l + 1) / 2
  if ord(data[p]) == 102:
    p += 1
    year = 2000 + ord(data[p]); p += 1
    month = ord(data[p]); p += 1
    day = ord(data[p]); p += 1
    hour = ord(data[p]); p += 1
    minute = ord(data[p]); p += 1
    second = ord(data[p]); p += 1
    p += 2
    ret['timefrom'] = "%04d-%02d-%02dT%02d:%02d:%02d" % (year, month, day, hour, minute, second)
  if ord(data[p]) == 103:
    p += 9 # finish date
  if ord(data[p]) == 104:
    p += 4 # tarif impulses
  if ord(data[p]) == 105:
    p += 3 # base service
  if ord(data[p]) == 106:
    p += 2 # ext service of initiator
  if ord(data[p]) == 107:
    p += 2 # ext service of called
  if ord(data[p]) == 108:
    p += 3 # abonent admin
  if ord(data[p]) == 109:
    num_l = ord(data[p+1])
    p += (num_l + 1) / 2
  if ord(data[p]) == 110:
    if USE_TRUNK_OUT_FROM_110:
      ret['trunk_out'] = "%u" % ord(data[p+1])
    p += 2
  if ord(data[p]) == 111:
    p += 2 # tarif direction
  if ord(data[p]) == 112:
    ret['cause'] = ord(data[p])
    p += 2
  if ord(data[p]) == 113:
    v = [ ord(x) for x in data[p:p+1+8] ]
    ret['trunk_in'] = "%u-%u-%u-%u-%u" % ( (v[1] << 8) + v[2], (v[3] << 8) + v[4], v[5], (v[6] << 8) + v[7], v[8] )
    p += 9
  if ord(data[p]) == 114:
    if USE_TRUNK_OUT_FROM_110:
      v = [ ord(x) for x in data[p:p+1+8] ]
      ret['trunk_out'] = "%u-%u-%u-%u-%u" % ( (v[1] << 8) + v[2], (v[3] << 8) + v[4], v[5], (v[6] << 8) + v[7], v[8] )
    p += 9
  if 'trunk_in' in ret and 'trunk_out' in ret:
    ret['direction'] = 254
  elif 'trunk_in' in ret:
    ret['direction'] = 0
  elif 'trunk_out' in ret:
    ret['direction'] = 1
  elif r.flags9 & 0x02:
    ret['direction'] = 1
  else:
    ret['direction'] = 0
  if ord(data[p]) == 115:
    p += 1
    v = 0
    v = v * (2**8) + ord(data[p]); p += 1
    v = v * (2**8) + ord(data[p]); p += 1
    v = v * (2**8) + ord(data[p]); p += 1
    v = v * (2**8) + ord(data[p]); p += 1
    if v > 0 and not (r.flags1 & 0x08):
      print >> sys.stderr, "Setting duration = 0 for failed call"
      v = 0
    ret['duration'] = int( (v + 500) / 1000 )
  if ord(data[p]) == 116:
    p += 4 # control sum
  if ord(data[p]) == 117:
    p += 10 # BGID, CGID
  if ord(data[p]) == 118:
    p += ord(data[p+1]) # Carrier Access Code
  if ord(data[p]) == 119:
    p += 2
    num_l = ord(data[p])
    p += 1
    print >> sys.stderr, "Num C = %s" % get_bcd( data[p:], 0, num_l )
  if ord(data[p]) == 120:
    p += ord(data[p+1]) # Prepaid account recharge data
  if ord(data[p]) == 121:
    ret['cause'] = (ord(data[p+2]) << 8) + ord(data[p+3])
    p += ord(data[p+1])
  if 'timefrom' not in ret:
    print >> sys.stderr, "Connect time is undefined. Parse as failed call."
    ret['timefrom'] = datetime.datetime.now().strftime( "%Y-%m-%dT%H:%M:%S" )
    ret['duration'] = 0
  if seq > 1:
    if not (r.flags1 & 0x20):
      print >> sys.stderr, "No 'Charging by AMA' flag set (F6 = 0), ignored"
      return []
    if ret['uniqueid'] in cache:
      print >> sys.stderr, "Found in cache by Call Id"
      last = cache[ret['uniqueid']]
      if ret['timefrom'] != last['timefrom']:
        last['duration'] += ret['duration']
        print >> sys.stderr, "Duration added"
      elif ret['duration'] > last['duration']:
        last['duration'] = ret['duration']
      if seq == 2:
        last['timefrom'] = ret['timefrom']
        print >> sys.stderr, "Timefrom replaced"
      elif seq == 4:
        ret = last
        del cache[ret['uniqueid']]
        print >> sys.stderr, "Erased"
    else:
      if seq != 2:
        print >> sys.stderr, "Start record missed for call with Call Id = %s" % ret["uniqueid"]
      if seq != 4:
        cache[ret['uniqueid']] = ret
  if seq in [1,4]:
    if 'cause' in ret and ret['cause'] == -1:
      if not (r.flags1 & 0x20):
        print >> sys.stderr, "F6 = 0, no disconnect cause found. Record ignored."
        return []
      ret['cause'] = 0
    return [ret]
  else:
    print >> sys.stderr, "Intermediate CDR skipped"
    return []

cache = {}
while True:
  data = get_data()
  if( data is None ):
    break
  calls = parse_data( data, cache );
  for call in calls:
    print ';'.join( [ "%s=%s" % ( x, str(call[x]) ) for x in call ] ) + ';'

