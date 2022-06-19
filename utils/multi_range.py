from typing import Sequence

class MultipleRange:
  def __init__(self, stops: Sequence[int]):
    self.stops = stops[:]
    self.num = len(stops)
    self.current = [0] * self.num
    if self.num > 0:
      self.current[0] = -1

  def __iter__(self):
    return self
  
  def __next__(self):
    for i in range(self.num):
      self.current[i] += 1
      if self.current[i] < self.stops[i]:
        return tuple(self.current)
      self.current[i] = 0
    raise StopIteration()