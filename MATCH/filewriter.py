import threading
import time

DATA = 0
TIME = 1
IGNORE = 0
FILENAME = 2

class FileWriter(threading.Thread):
    
    def __init__(self):
        #threading.Thread.__init__(self)
        super().__init__()
        self.condition = threading.Condition()
        self.buffer = []


    def run(self):
        duration = IGNORE
        while(True):
            ready = 0
            
            with self.condition:
                while not self.buffer:
                    self.condition.wait()
                if self.buffer:
                    task = self.buffer.pop(0)
                    duration = task[TIME]
                    filename = task[FILENAME]
                    ready = True
            
            if ready:
                try:
                    target = open(filename, "w", encoding="utf-8")
                except OSError:
                    print(f"Error -  Unable to open {filename}")
                    ready = False

            if ready:
                with target:
                    target.write(task[DATA])
                    target.flush()
                    if duration != IGNORE:
                        time.sleep(duration)
                        duration = IGNORE
                        target.seek(0)
                        target.truncate()
                        target.flush()
                    ready = False
        
    
    def queue(self, data, time, filename):
        with self.condition:
            self.buffer.append([data, time, filename])
            self.condition.notify()
    
