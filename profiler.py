# Copyright (c) Skye Cobile <skye.cobile@outlook.com> 2020, Germany
# SEE LICENSE
# -----------
# Simple Profiler for finer breakdown of the program's performance.

from time import perf_counter_ns
import sys

class Profiler:
    def __init__(self):
        # Collection of ProfilerSegment instances
        self.segments = []
    
    def segment(self, name = "<unnamed segment>"):
        segment = ProfilerSegment(name)
        self.segments.append(segment)
        return segment
    
    def dump(self, io = sys.stdout):
        for segment in self.segments:
            segment.dump(0, io)

class ProfilerSegment:
    def __init__(self, name = "<unnamed segment>"):
        self.name = name
        self.subsegments = []
        self._start = -1 # time.perf_counter_ns() does not have a guaranteed reference point, so knowing start and end times is useless.
        self.diff   = -1
    
    def __enter__(self):
        self._start = perf_counter_ns()
        return self
    
    def __exit__(self, *args, **kwargs):
        self.diff = perf_counter_ns() - self._start
    
    def segment(self, name = "<unnamed segment>"):
        segment = ProfilerSegment(name)
        self.subsegments.append(segment)
        return segment
    
    def dump(self, level, io):
        # Print ancestor relation
        # Skips root and first child
        for i in range(1, level):
            io.write('| ')
        
        # Print child relation
        if level > 0:
            io.write('|-')
        
        io.write(f'{self.name}: {self.diff / 10**6}ms\n')
        for segment in self.subsegments:
            segment.dump(level + 1, io)
