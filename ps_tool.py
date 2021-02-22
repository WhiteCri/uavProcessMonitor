import psutil
import time
from subprocess import check_output


class ProcessLogger:
    def __init__(self, proc_name):
        # process life managing mambers
        self.found = False
        self.terminated = False
        self.proc_name = proc_name

    def searchProc(self):
        '''
        if process is found with name 'proc_name', it returns pid
        :return: pid if found, -1 else
        '''
        pid_str = check_output(['pidof', self.proc_name])
        try:
            pid = int(pid_str)
        except ValueError: # not found process
            return -1
        return pid


    def doInit(self, pid):
        self.found = True
        self.p = psutil.Process(pid)
        self.start_time = self.p.create_time()
        self.data = {'cpu': [], 'memory': [], 'stamp': []}

        print('New Process Detected : {}'.format(self.proc_name))

        #initialize
        self.p.cpu_percent()

    def logCpuMemory(self):
        self.data['cpu'].append(self.p.cpu_percent())
        self.data['memory'].append(self.p.memory_percent())
        self.data['stamp'].append(time.time())
        self.printLastLog()

    def printLastLog(self):
        print("[{}] cpu : {:.2f}, memory : {:.2f}, stamp : {:.0f}"
              .format(self.proc_name, self.data['cpu'][-1], self.data['memory'][-1], self.data['stamp'][-1]))
