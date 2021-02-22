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
        self.server = False

        # members for calculating GB
        self.GB = 1024**3
        if self.proc_name == 'server':
            self.found = True
            self.server = True
            self.n_cpu = psutil.cpu_count()
            self.data = {'cpu_percent': [], 'memory_percent': [], 'memory_GB': [], 'stamp': []}
            self.n_data = 0
            self.start_time = time.time()

            psutil.cpu_percent()

    def search_proc(self):
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

    def do_init(self, pid):
        self.found = True
        self.p = psutil.Process(pid)
        self.start_time = self.p.create_time()
        self.data = {'cpu_percent': [], 'memory_percent': [], 'memory_GB': [], 'stamp': []}
        self.n_data = 0
        print('New Process Detected : {}'.format(self.proc_name))

        #initialize
        self.p.cpu_percent()

    def log_cpu_memory(self):
        if self.proc_name == 'server':
            self.data['stamp'].append(time.time())
            self.data['cpu_percent'].append(psutil.cpu_percent() * self.n_cpu)
            # see https://psutil.readthedocs.io/en/latest/#psutil.virtual_memory
            # I calculated the unavailable memory that can not be given instantly
            # because the system going to swap in advance
            mem = psutil.virtual_memory()
            gap_GB = 1.0 * (mem.total - mem.available) / self.GB
            gap_percent = 1.0 * (mem.total - mem.available) / mem.total * 100
            self.data['memory_percent'].append(gap_percent)
            self.data['memory_GB'].append(gap_GB)
            self.n_data += 1
            self.print_last_log()

            return

        if not self.terminated:
            try:
                self.data['stamp'].append(time.time())
                self.data['cpu_percent'].append(self.p.cpu_percent())
                self.data['memory_percent'].append(self.p.memory_percent())
                self.data['memory_GB'].append(1.0 * self.p.memory_info().rss / self.GB)
                self.n_data += 1

                self.print_last_log()
            except psutil.NoSuchProcess:
                self.terminated = True
                print('[{}] process terminated'.format(self.proc_name))

    def print_last_log(self):
        print("[{}] cpu : {:.2f}%, memory : {:.2f}% / {:.2f}GB, stamp : {:.0f}"
              .format(self.proc_name, self.data['cpu_percent'][-1],
                      self.data['memory_percent'][-1], self.data['memory_GB'][-1],
                      self.data['stamp'][-1]))
