## This program should run with root previlege, depending on your cmd
## this program uses memory with linear increasing speed.

import ps_tool
import os
import threading
import time
import proc_names
PROCESS_UPDATE_PERIOD = 1 # second


class ProcessMonitor:
    def __init__(self, exe_names):
        self.p_infos = [ps_tool.ProcessLogger(exe_name) for exe_name in exe_names]

    def track_process(self, pid):
        self.p_infos.append(ProcessMonitor.ProcessInfo(pid))

    def update(self):
        n_terminated = 0
        for p_info in self.p_infos:
            if p_info.terminated:
                n_terminated += 1
            elif p_info.found:
                p_info.logCpuMemory()
            else: # not found
                pid = p_info.searchProc()
                if pid != -1:
                    p_info.doInit(pid)
                else :
                    print('not found {}'.format(p_info.proc_name))
        if n_terminated == len(self.p_infos):
            return False
        else:
            return True

    def gen_dir(self, dir_name='proc_info'):
        self.path = os.path.join(os.getcwd(), dir_name)
        if not os.path.isdir(self.path):
            os.mkdir(self.path)

    def save_csv(self):
        # gen directory
        self.gen_dir()

        for p_info in self.p_infos:
            if not p_info.csv_saved:
                filename = p_info.proc_name + '.csv'
                with open(self.path + '/' + filename, 'w') as f:
                    f.write('timestamp(period={}),cpu(%),memory(GB),memory(%)\n'.format(PROCESS_UPDATE_PERIOD))
                    for i in range(p_info.n_data):
                        line = str(p_info.data['stamp'][i]) + ',' + \
                               str(p_info.data['cpu_percent'][i]) + ',' + \
                               str(p_info.data['memory_GB'][i]) + ',' + \
                               str(p_info.data['memory_percent'][i]) + '\n'
                        f.write(line)

    def save_box_and_whisker_plot(self):
        self.gen_dir()
        pass

def save_process_info():
    global process_monitor
    last_time = time.time()

    # update proc info
    while True:
        dt = (time.time() - last_time)
        if dt >= PROCESS_UPDATE_PERIOD:
            # update processes
            last_time = time.time()
            terminated_all = process_monitor.update()
            if not terminated_all:
                break
        else:
            time.sleep(1/1000.0) #1ms

    # save as csv
    print('save as csv...')
    process_monitor.save_csv()

    # save as plot
    print('save as plot...')


if __name__=='__main__':
    process_monitor = ProcessMonitor(proc_names.exe_names)

    # append cpu and memory usage according to the cycle
    thr = threading.Thread(target=save_process_info)
    thr.daemon = True
    thr.start()
    thr.join()

    '''
    while True:
        time.sleep(1)
        ## sig child...
        ## exit handling...
    '''