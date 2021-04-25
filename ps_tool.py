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
        self.server = False
        self.processes = []

        # members for calculating GB
        self.GB = 1024**3

        # server initialization
        if self.proc_name == 'server':
            self.found = True
            self.server = True
            self.n_cpu = psutil.cpu_count()
            self.data = {'cpu_percent': [], 'memory_percent': [], 'memory_GB': [], 'stamp': []}
            self.n_data = 0
            psutil.cpu_percent()

    def save_csv(self, target_dir):
        if not self.csv_saved:
            filename = self.proc_name + '.csv'
            print('saving {}...'.format(filename))
            with open(target_dir + '/' + filename, 'w') as f:
                f.write('timestamp,cpu(%),memory(GB),memory(%)\n')
                for i in range(self.n_data):
                    line = str(self.data['stamp'][i]) + ',' + \
                           str(self.data['cpu_percent'][i]) + ',' + \
                           str(self.data['memory_GB'][i]) + ',' + \
                           str(self.data['memory_percent'][i]) + '\n'
                    f.write(line)

    def search_proc(self):
        '''
        if process is found with name 'proc_name', it returns pid
        :return: pid if found, -1 else
        '''
        try:
            pid_str = check_output(['pidof', self.proc_name])
        except CalledProcessError: # not found process
            print(f'process [{self.proc_name}] not found')
            return -1
        pid_str_list = pid_str.decode('ascii').split(' ') # byte to string, slice by space
        pids = [int(pid) for pid in pid_str_list]
        return pids

    def do_init(self):
        pids = self.search_proc()
        if pids == -1:
            return

        self.found = True
        for pid in pids: # multiprocess handling
            self.processes.append(psutil.Process(pid))
            self.data = {'cpu_percent': [], 'memory_percent': [], 'memory_GB': [], 'stamp': []}
            self.n_data = 0
        print('New Process Detected : {}'.format(self.proc_name))

        # initialize
        for p in self.processes:
            p.cpu_percent()

        if len(self.processes) >= 2:
            print(f'######### {self.proc_name} : multi process memory usage tracking is not exact, since some memories are shared ########')

    def log_cpu_memory(self):
        if self.proc_name == 'server':
            self.data['stamp'].append(time.time())
            # calc cpu
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
            not_found = 0
            try:
                cpu = 0
                mem_percent = 0
                mem_abs = 0
                for p in self.processes:
                    cpu += p.cpu_percent()
                    mem_percent += p.memory_percent()
                    mem_abs += 1.0 * p.memory_info().rss / self.GB

                self.data['stamp'].append(time.time())
                self.data['cpu_percent'].append(cpu)
                self.data['memory_percent'].append(mem_percent)
                self.data['memory_GB'].append(mem_abs)
                self.n_data += 1

                self.print_last_log()
            except psutil.NoSuchProcess:
                not_found += 1

            if not_found == len(self.processes):
                self.terminated = True
                print('[{}] process terminated'.format(self.proc_name))

    def print_last_log(self):
        print("[{}] cpu : {:.2f}%, memory : {:.2f}% / {:.2f}GB, stamp : {:.0f}"
              .format(self.proc_name, self.data['cpu_percent'][-1],
                      self.data['memory_percent'][-1], self.data['memory_GB'][-1],
                      self.data['stamp'][-1]))
