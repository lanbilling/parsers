#!/usr/bin/python

import sys
import os

fields = [
  ("Serial Number",4),
  ("Ticket Type",1),
  ("Checksum",1),
  ("Partial Record Indicator",0.25),
  ("Clock Changed Flag",0.125),
  ("Free Flag",0.125),
  ("Validity",0.125),
  ("Call Attempt Flag",0.125),
  ("Complaint Flag",0.125),
  ("Centralized Charging Flag",0.125),
  ("PPS Flag",0.125),
  ("Charging Method",0.25),
  ("NP Call Flag",0.125),
  ("Payer",0.5),
  ("Conversation End Time",6),
  ("Conversation Duration",4),
  ("Caller Seizure Duration",4),
  ("Called Seizure Duration",4),
  ("Incomplete Call Watch",0.25),
  ("Caller ISDN Access",0.125),
  ("Called ISDN Access",0.125),
  ("ISUP Indication",0.125),
  ("Reserved",0.375),
  ("Charging Number Address Nature",0.5),
  ("Caller Number Address Nature",0.5),
  ("Connected Number Address Nature",0.5),
  ("Called Number Address nature",0.5),
  ("Charging Number DNSet",1),
  ("Charging Number",10),
  ("Caller Number DNSet",1),
  ("Caller Number",10),
  ("Connected Number DNSet",1),
  ("Connected Number",10),
  ("Called Number DNSet",1),
  ("Called Number",10),
  ("Dialed Number",12),
  ("CENTREX Group Number",2),
  ("Caller CENTREX Short Number",4),
  ("Called CENTREX Short Number",4),
  ("Caller Module Number",1),
  ("Called Module Number",1),
  ("Incoming Trunk Group Number",2),
  ("Outgoing Trunk Group Number",2),
  ("Incoming Subroute Number",2),
  ("Outgoing Subroute Number",2),
  ("Caller Device Type",1),
  ("Called Device Type",1),
  ("Caller Port Number",2),
  ("Called Port Number",2),
  ("Caller Category",1),
  ("Called Category",1),
  ("Call Type",0.5),
  ("Service Type",0.5),
  ("Supplementary Service Type",1),
  ("Charging Case",2),
  ("Tariff",2),
  ("Charging Pulse",4),
  ("Fee",4),
  ("Balance",4),
  ("Bearer Service",1),
  ("Teleservice",0.5),
  ("Release Party",0.375),
  ("Release Index",1.125),
  ("Release Cause Value",1),
  ("UUS1 Count",1),
  ("UUS2 Count",1),
  ("UUS3 Count",1),
  ("OPC",4),
  ("DPC",4),
  ("B_num",0.625),
  ("Reserved3",0.375),
  #("Reserved",78),
  #("Add up",154)
]


def parse( data ):
  n = 0
  skip_bits = 0
  ret = {}
  i = 0
  for x in fields:
    i += 1
    nm = x[0]
    sz = x[1]
    if( sz < 1 or type(sz) != type(int()) ):
      skip_bits += int( 8 * sz )
      #print 'skip bits', skip_bits
      continue
    #print 'Offset', n
    if( skip_bits >= 8 ):
      n += int(skip_bits/8)
      skip_bits -= int(skip_bits/8)
    #print 'Offset', n
    if( len(data) < n ):
      #print 'end'
      break
    d = data[n:n+sz]
    n += sz
    ints = [ ord(y) for y in d ]
    #print i, nm, sz, ints, ":".join( [ "%02x" % z for z in ints ] )
    ret[ nm ] = ints
  #print ret
  #print n
  return ret

def unpack( v ):
  res = ''
  for x in [ ( (x & 0xf0) >> 4, x & 0x0f ) for x in v ]:
    if not x[0] >= 0x0f:
      res += chr( ord('0') + x[0] )
    if not x[1] >= 0x0f:
      res += chr( ord('0') + x[1] )
  return res

def formate( res ):
  lines = []
  dt = res['Conversation End Time']
  dur = res['Caller Seizure Duration']
  dur_len = 0
  for x in reversed( dur ):
    if x:
      dur_len *= 0x100
      dur_len += x
  dur_len /= 100
  lines += [ 'timefrom=%04d-%02d-%02dT%02d:%02d:%02d' % ( 2000 + dt[0], dt[1], dt[2], dt[3], dt[4], dt[5] ) ]
  lines += [ 'numfrom=' + unpack( res['Charging Number'] ) ]
  lines += [ 'numto=' + unpack( res['Connected Number'] ) ]
  lines += [ 'duration=%s' % ( dur_len, ) ]
  return ";".join( lines )

def pprint( res, nm ):
  print nm, res[nm], ":".join( [ "%02x" % z for z in res[nm]] )

data = sys.stdin.read()
nn = 0
sz = 0x9c - 2
while len(data) >= (nn+1) * sz:
  p = data[nn * sz: (nn+1) * sz]
  res = parse( p )
  line = formate( res )
  #pprint( res, 'Conversation End Time' )
  #pprint( res, 'Charging Number' )
  #pprint( res, 'Caller Seizure Duration' )
  #pprint( res, 'Connected Number' )
  #print 'Line: ', line
  #print '=' * 10
  print line
  nn += 1

