import psutil
import time
from subprocess import check_output
from subprocess import CalledProcessError

class ProcessLogger:
    def __init__(self, proc_name):
        # process life managing mambers
        self.found = False
        self.terminated = False
        self.proc_name = proc_name
        self.csv_saved = False
        self.plt_saved = False

        # members for calculating GB
        self.GB = 1024**3


    def searchProc(self):
        '''
        if process is found with name 'proc_name', it returns pid
        :return: pid if found, -1 else
        '''
        try:
            pid_str = check_output(['pidof', self.proc_name])
        except CalledProcessError: # not found process
            return -1
        pid = int(pid_str)
        return pid


    def doInit(self, pid):
        self.found = True
        self.p = psutil.Process(pid)
        self.start_time = self.p.create_time()
        self.data = {'cpu_percent': [], 'memory_percent': [], 'memory_GB': [], 'stamp': []}
        self.n_data = 0
        print('New Process Detected : {}'.format(self.proc_name))

        #initialize
        self.p.cpu_percent()

    def logCpuMemory(self):
        if not self.terminated:
            try:
                self.data['stamp'].append(time.time())
                self.data['cpu_percent'].append(self.p.cpu_percent())
                self.data['memory_percent'].append(self.p.memory_percent())
                self.data['memory_GB'].append(1.0 * self.p.memory_info().rss / self.GB)
                self.n_data += 1

                self.printLastLog()
            except psutil.NoSuchProcess:
                self.terminated = True
                print('[{}] process terminated'.format(self.proc_name))

    def printLastLog(self):
        print("[{}] cpu : {:.2f}%, memory : {:.2f}% / {:.2f}GB, stamp : {:.0f}"
              .format(self.proc_name, self.data['cpu_percent'][-1],
                      self.data['memory_percent'][-1], self.data['memory_GB'][-1],
                      self.data['stamp'][-1]))
