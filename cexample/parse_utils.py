"""
 *   BSD LICENSE
 *
 *   Copyright (c) Intel Corporation.
 *   All rights reserved.
 *
 *   Author: Anjaneya Chagam <anjaneya.chagam@intel.com>
 *
 *   Redistribution and use in source and binary forms, with or without
 *   modification, are permitted provided that the following conditions
 *   are met:
 *
 *     * Redistributions of source code must retain the above copyright
 *       notice, this list of conditions and the following disclaimer.
 *     * Redistributions in binary form must reproduce the above copyright
 *       notice, this list of conditions and the following disclaimer in
 *       the documentation and/or other materials provided with the
 *       distribution.
 *     * Neither the name of Intel Corporation nor the names of its
 *       contributors may be used to endorse or promote products derived
 *       from this software without specific prior written permission.
 *
 *   THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
 *   "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
 *   LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
 *   A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
 *   OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
 *   SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
 *   LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
 *   DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
 *   THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
 *   (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
 *   OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""

import sys
import os
import re
import dateutil.parser
import datetime
from datetime import timedelta
import numpy as np
import getopt
import string
import threading
from parse import *
from sys import stdout
try:
  from queue import Queue
  import babeltrace
except:
  from Queue import Queue


"""
Wrapper for calling object function method
"""
class FuncThread(threading.Thread):
  def __init__(self, method, *args):
    self._method = method
    self._args = args
    threading.Thread.__init__(self)

  def run(self):
    self._method(*self._args)

"""
Common functions
"""
class Util(object):
  @staticmethod
  def get_usecs_elapsed(b_ts, e_ts):
    if isinstance(b_ts, str) and isinstance(e_ts, str):
      d1 = dateutil.parser.parse(b_ts)
      d2 = dateutil.parser.parse(e_ts)
      return ((d2-d1).total_seconds())*1000000
    elif ((isinstance(b_ts, int) or isinstance(b_ts, float)) and 
          (isinstance(e_ts, int) or isinstance(e_ts, float))): #nanoseconds since Epoch   
      return (e_ts-b_ts)/1000
    else: 
      return ((e_ts-b_ts).total_seconds())*1000000

"""
FuncStack provides abstraction for call stack as well as ordered tree traversal
to consolidate duplicate sub stacks
"""
class FuncStack(object):
  def __init__(self, parent, level, func, file, line):
    self.parent = parent
    self.children = list()
    self.level = level
    self.func = func
    self.file = file
    self.line = line
    self.ts = list()

  def key(self):
    return "%s:%s" % (self.func, self.file)

  def insert(self, node):
    self.children.append(node)

  def add_enter_ts(self, ts):
    self.ts.append([ts])

  def add_exit_ts(self, ts):
    self.ts[-1].append(ts)

  def parent(self):
    return self.parent

  def dump(self):
    print("%d,%s,%s,%s,%s,[children:%d]" % (self.level, self.func, self.file, self.line, self.ts, len(self.children)))

  def is_leaf(self):
    if len(self.children) == 0:
      return True
    else:
      return False

  def traverse(self):
    self.dump()
    for n in self.children:
      n.traverse()

  def coompute_and_dump_stats(self, ofd, detail_stats):
    lat = list()
    for t in self.ts:
      s = Util.get_usecs_elapsed(t[0], t[1])
      lat.append(s)
    a = np.array(lat)
    sk = "%s%s:%s:%s:%s" % ('    '*self.level, 'ENTRY', self.func, self.file, self.line)
    if detail_stats:
        ofd.write("%s,%s,%.2f,%.2f,%.2f,%.2f,%.2f,%.2f,%.2f\n" % (sk, a.size, np.average(a), np.median(a),
                  np.percentile(a, 90), np.percentile(a, 95), np.percentile(a, 99), np.std(a), np.var(a)))
    else:
        ofd.write("%s,%s,%.2f\n" % (sk, a.size, np.average(a)))

  def dump_exit_marker(self, ofd, detail_stats):
    sk = "%s%s:%s:%s" % ('    '*self.level, 'EXIT', self.func, self.file)
    ofd.write("%s\n" % (sk))
    
  def dump_stats(self, ofd, detail_stats):
    self.coompute_and_dump_stats(ofd, detail_stats)
    for n in self.children:
      n.dump_stats(ofd, detail_stats)
    self.dump_exit_marker(ofd, detail_stats)
    
  def __eq__(self, right):
    if self.level == right.level and self.func == right.func and self.file == right.file:
      if len(self.children) == len(right.children):
        for i in range(len(self.children)):
          if self.children[i] == right.children[i]:
            continue
          else:
            return False
        return True
      else:
        return False
    else:
      return False
    
  def merge(self, y):
    self.ts.extend(y.ts)
    y.ts = list()
    for i in range(len(self.children)):
      self.children[i].merge(y.children[i])
    y.children = list()

  def trim(self):
    # pick non leaf nodes and traverse until you find leaf nodes to merge
    nlfnodes = [c for c in self.children if not c.is_leaf()]
    for nl in nlfnodes:
      nl.trim()

    for x in range(len(self.children)):
      for y in range(x+1, len(self.children)):
        n1 = self.children[x]
        n2 = self.children[y]
        if n1 == n2:
          n1.merge(n2)

    # get rid of all children who do not have any time stamps
    self.children = [c for c in self.children if len(c.ts) > 0]


class ParseError(RuntimeError):
 def __init__(self, arg):
    self.args = arg

"""
Parses one event
"""
class EventParser(object):
  def __init__(self, event_str):
    self.event_str = event_str
    self.attrs = dict()
    base_fmt='[{ts}]{}functrace:{id}: { cpu_id = {cpu_id} }, { pthread_id = {pthread_id}, ' \
      'vpid = {vpid}, procname = "{procname}" }, '
    self.enter_fmt = base_fmt + '{ file = "{file}", func = "{func}", line = {line} }'
    self.exit_fmt = base_fmt + '{ file = "{file}", func = "{func}" }'

  def parse_short(self):
    res = parse('{} functrace:{id}: { cpu_id = {}}, { pthread_id = {pthread_id}, vpid = {vpid}, procname = {}}', self.event_str)
    if res:
      self.attrs.update(res.named)
    return res

  def parse(self):
    # get event and do the parsing based on event type
    res = parse('{}functrace:{id}: { cpu_id{}', self.event_str)

    if res:
      self.attrs.update(res.named)
      if self.attrs['id'] == 'func_enter':
        res = parse(self.enter_fmt, self.event_str)
      elif self.attrs['id'] == 'func_exit':
        res = parse(self.exit_fmt, self.event_str)
      else:
        return None
      if res:
        self.attrs.update(res.named)
    return res

  # expect caller to handle exceptions
  def __getattr__(self, item):
    return self.attrs[item]

  def dump(self):
    print("%s" % (self.attrs))

"""
Parse function trace events
"""
class FuncEventTraceParser(object):
  def __init__(self, file, detail_stats = 0):
    self.src_file = file
    self.stacks_per_tid_file = dict()
    self.detail_stats = detail_stats 
    self.long_hdr = "state:function:file:line,count,avg(usecs),med(usecs),90(usecs),95(usecs),99(usecs),std(usecs),var(usecs)\n"
    self.short_hdr = "state:function:file:line,count,avg(usecs)\n"

  def add_stack(self, stacks, s):
    for n in stacks:
      if n == s:
        n.merge(s)
        return
    stacks.append(s)

  def parse_thread_trace_file(self, file):
    print("computing stats for file '%s'" % (file))

    level=0
    root=None
    parent=None
    stack = list()
    stacks = list()
    with open(file, 'r') as f:
      for line in f:
        event = EventParser(line)
        if event.parse():
          if event.attrs['id'] == 'func_enter':
            node = FuncStack(parent, level, event.attrs['func'], event.attrs['file'], event.attrs['line'])
            node.add_enter_ts(event.attrs['ts'])
            if level == 0:
              root = node
            else:
              parent.insert(node)
            parent = node
            stack.append(node)
            level += 1
          elif event.attrs['id'] == 'func_exit':
            if level == 0: # means out of line marker, ignore
                continue
            level -= 1
            node = stack.pop()
            node.add_exit_ts(event.attrs['ts'])
            parent = node.parent

            if level == 0:
              root.trim()
              self.add_stack(stacks, root)
              root=None
              parent=None
              stack=list()

    # this may need to be locked to be multi-threaded safe
    self.stacks_per_tid_file[file] = stacks
                    
  """
  create separate files for each thread - maintain sequence based on what is observed in source file
  """

  def split_file_by_tid(self):
    threads={}
    sequence=0
    self.file_list={}
    with open(self.src_file, 'r') as f:
      for line in f:
        event = EventParser(line)
        if event.parse_short() and (event.attrs['id'] == 'func_enter' or event.attrs['id'] == 'func_exit'):
            tid =  event.attrs['pthread_id']
            if not threads.has_key(tid):
                sequence=sequence+1
                threads[tid] = sequence
            new_file='%s__%d_%s' % (self.src_file,threads[tid],tid)
            self.file_list[new_file] = ''
            with open(new_file, 'a') as n:
                n.write(line)


  def extract_per_thread_stack(self):
    # for each file, do the indent
    threads = []
    for temp_file in self.file_list.keys():
      thr = FuncThread(self.parse_thread_trace_file, temp_file)
      thr.start()
      threads.append(thr)
    
    # wait for all threads to complete
    for t in threads:
      t.join()

    # remove temp files
    for temp_file in self.file_list.keys():
      os.remove(temp_file)

  def dump_stacks(self):
    stack_file="%s.perf.csv" % self.src_file
    sfd = open(stack_file, 'w')
    stacks = list()
    
    # create unique stacks
    for file in self.stacks_per_tid_file:
      for s in self.stacks_per_tid_file[file]:
        self.add_stack(stacks, s)
    
    # write header to file
    if self.detail_stats:
      sfd.write(self.long_hdr)
    else:
      sfd.write(self.short_hdr)

    # write each stack to file
    for stack in stacks:
      stack.dump_stats(sfd, self.detail_stats)


