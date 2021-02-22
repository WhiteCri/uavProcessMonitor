## This program should run with root previlege, depending on your cmd
## this program uses memory with linear increasing speed.
## some of tip datas are skipped because of poor synchronization, but i'm lazy to fix that..

import ps_tool
import os
import threading
import time
import proc_names
import signal
import sys
import argparse
import matplotlib.pyplot as plt

TW_EXIT_CODE = 97
PROCESS_UPDATE_PERIOD = 0.2 # second
sigint_captured = False
flush_done = False

class ProcessMonitor:
    def __init__(self, names, dir_name=None):
        self.p_infos = [ps_tool.ProcessLogger(proc_name) for proc_name in names]
        self.dir_name = 'proc_info' if dir_name is None else dir_name

    def track_process(self, pid):
        self.p_infos.append(ProcessMonitor.ProcessInfo(pid))

    def update(self):
        '''
        :return: if every process terminated except server
        '''
        n_terminated = 0
        for p_info in self.p_infos:
            if p_info.terminated:
                n_terminated += 1
            elif p_info.found:
                p_info.log_cpu_memory()
            else: # not found
                pid = p_info.search_proc()
                if pid != -1:
                    p_info.do_init(pid)
                else :
                    print('not found {}'.format(p_info.proc_name))
        if n_terminated == len(self.p_infos) - 1:
            return False
        else:
            return True

    def gen_dir(self):
        self.path = os.path.join(os.getcwd(), self.dir_name)
        if not os.path.isdir(self.path):
            os.mkdir(self.path)

    def save_csv(self):
        # gen directory
        self.gen_dir()

        for p_info in self.p_infos:
            if p_info.proc_name is not 'server':
                if not p_info.found:
                    continue

            if not p_info.csv_saved:
                filename = p_info.proc_name + '.csv'
                print('saving {}...'.format(filename))
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


def sigint_handler(sig, frame):
    global sigint_captured
    sigint_captured = True

    global flush_done
    while not flush_done:
        time.sleep(0.01) # 10ms

    print('flush done detected in sigint_handler')
    sys.exit(TW_EXIT_CODE)


def save_process_info():
    global process_monitor
    global sigint_captured

    last_time = time.time()

    # update proc info
    while not sigint_captured:
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
    process_monitor.save_csv()

    # save as plot
    print('save plot...')

    global flush_done
    flush_done = True

    sys.exit(TW_EXIT_CODE)

if __name__=='__main__':
    parser = argparse.ArgumentParser(description='Simple Process cpu & memory tracker')
    parser.add_argument('--dir-name', type=str,
                        help='name of result folder')

    args = parser.parse_args()
    process_monitor = ProcessMonitor(proc_names.exe_names, args.dir_name)

    # set sigint handler for ctrl+C
    signal.signal(signal.SIGINT, sigint_handler)

    # saving thread start
    thr = threading.Thread(target=save_process_info)
    thr.daemon = True
    thr.start()

    # I maintained this software architecture for future use
    while True:
        time.sleep(1)
        if flush_done:
            sys.exit(TW_EXIT_CODE)
    '''
    while True:
        time.sleep(1)
        ## sig child...
        ## exit handling...
    '''