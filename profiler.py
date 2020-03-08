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
        
        # Track currently active segment so user code can simply call `segment` method to properly insert
        # a new segment.
        self.active_segment = None
    
    def segment(self, name = "<unnamed segment>"):
        if self.active_segment is None:
            segment = ProfilerSegment(self, name)
            self.segments.append(segment)
            return segment
        else:
            return self.active_segment.segment(name)
    
    def dump(self, io = sys.stdout):
        for segment in self.segments:
            segment.dump(0, io)

class ProfilerSegment:
    def __init__(self, profiler, name = "<unnamed segment>"):
        self.profiler = profiler
        self.name = name
        self.subsegments = []
        self._start = -1 # time.perf_counter_ns() does not have a guaranteed reference point, so knowing start and end times is useless.
        self.diff   = -1
        self._prev_active = None
    
    def __enter__(self):
        self._prev_active = self.profiler.active_segment
        self.profiler.active_segment = self
        self._start = perf_counter_ns()
        return self
    
    def __exit__(self, *args, **kwargs):
        self.diff = perf_counter_ns() - self._start
        self.profiler.active_segment = self._prev_active
    
    def segment(self, name = "<unnamed segment>"):
        segment = ProfilerSegment(self.profiler, name)
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
