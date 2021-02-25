## This program should run with root previlege, depending on your cmd
## this program uses memory with linear increasing speed.
## some of tip datas are skipped because of poor synchronization, but i'm lazy to fix that..

import psutil
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
PROCESS_UPDATE_PERIOD = 0.5 # second
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

    def save_ok(self):
        n_proc = len(self.p_infos)
        cnt = len([dummy.found for dummy in self.p_infos if dummy.found])
        return cnt == n_proc

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

    def save_plots(self):
        self.gen_dir()
        # I used not collected data in variable but csv data,
        # to make this function separate from others

        csv_names = [p_info.proc_name for p_info in self.p_infos]
        data = {csv_name: {'stamp': [], 'cpu_percent': [], 'memory_GB': [], 'memory_percent': []}
                for csv_name in csv_names}
        target_dir = os.path.join(os.getcwd(), self.dir_name) + '/'
        for csv_name in csv_names:
            target_file_path = target_dir + csv_name + '.csv'
            with open(target_file_path, 'r') as f:
                f.readline()
                data_csv = f.readlines()
                # 0 : stamp
                # 1 : cpu_percent
                # 2 : memory_GB
                # 3 : memory_percent
                data[csv_name]['stamp']             = [float(l.rstrip('\n').split(',')[0]) for l in data_csv]
                data[csv_name]['cpu_percent']       = [float(l.rstrip('\n').split(',')[1]) for l in data_csv]
                data[csv_name]['memory_GB']         = [float(l.rstrip('\n').split(',')[2]) for l in data_csv]
                data[csv_name]['memory_percent']    = [float(l.rstrip('\n').split(',')[3]) for l in data_csv]

        cpu_usage_str = 'Cpu Usage % (with {} cores)'.format(psutil.cpu_count())
        memory_usage_gb_str = 'Memory Usage GB'
        memory_usage_percent_str = 'Memory Usage % (with {} GB memory)'\
            .format(int(1.0*psutil.virtual_memory().total / 1024**3))

        # save box_and_whisker plot
        print('** note that box_and_whisker_plot ignores some outliers(fliers) **')
        print('draw cpu usage % box_and_whisker plot...')
        # plt.boxplot([data[csv_name]['cpu_percent'] for csv_name in csv_names], whis=50) # not detect outlier
        plt.boxplot([data[csv_name]['cpu_percent'] for csv_name in csv_names],
                    labels=csv_names, showfliers=False) # not show outlier
        plt.ylabel(cpu_usage_str)
        plt.xlabel('')
        plt.savefig(target_dir + 'Cpu_Usage_box_and_whiskers.png')

        plt.clf()
        print('draw memory usage GB box_and_whisker plot...')
        plt.boxplot([data[csv_name]['memory_GB'] for csv_name in csv_names],
                    labels=csv_names, showfliers=False)  # not show outlier
        plt.ylabel(memory_usage_gb_str)
        plt.savefig(target_dir + 'Memory_Usage_GB_box_and_whiskers.png')

        plt.clf()
        print('draw memory usage % box_and_whisker plot...')
        plt.boxplot([data[csv_name]['memory_percent'] for csv_name in csv_names],
                    labels=csv_names, showfliers=False)  # not show outlier
        plt.ylabel(memory_usage_percent_str)
        plt.savefig(target_dir + 'Memory_Usage_percent_box_and_whiskers.png')

        # save xy_plot. x is stamp, y is each data
        for csv_name in csv_names:
            stamp_begin_with_0 = [stamp - data[csv_name]['stamp'][0] for stamp in data[csv_name]['stamp']]

            print('draw {} cpu usage...'.format(csv_name))
            plt.clf()
            plt.plot(stamp_begin_with_0, data[csv_name]['cpu_percent'])
            plt.ylabel(cpu_usage_str)
            plt.xlabel('seconds')
            plt.xlim(stamp_begin_with_0[0], stamp_begin_with_0[-1])
            ylim = 100
            max_y = max(data[csv_name]['cpu_percent'])
            while ylim < max_y:
                ylim += 100
            plt.ylim(0, ylim)
            plt.savefig(target_dir + '{}_Cpu_Usage.png'.format(csv_name))

            print('draw {} memory usage GB...'.format(csv_name))
            plt.clf()
            plt.plot(stamp_begin_with_0, data[csv_name]['memory_GB'])
            plt.ylabel(memory_usage_gb_str)
            plt.xlabel('seconds')
            plt.savefig(target_dir + '{}_Memory_Usage_GB.png'.format(csv_name))

            print('draw {} memory usage %...'.format(csv_name))
            plt.clf()
            plt.plot(stamp_begin_with_0, data[csv_name]['memory_percent'])
            plt.ylabel(memory_usage_percent_str)
            plt.xlabel('seconds')
            plt.savefig(target_dir + '{}_Memory_Usage_percent.png'.format(csv_name))

        ## plot everything in one-shot
        # calc stamp start with server time
        first_start_time = data[csv_names[0]]['stamp'][0]
        first_end_time = data[csv_names[0]]['stamp'][-1]
        # plot cpu usages
        print('draw every_process cpu usage...'.format(csv_name))
        plt.clf()
        for csv_name in csv_names:
            stamp_begin_with_first_0 = [stamp - first_start_time for stamp in data[csv_name]['stamp']
                                        if first_start_time <= stamp <= first_end_time]
            cpu_usages = [cpu_percent for cpu_percent in data[csv_name]['cpu_percent']]
            cpu_usages = cpu_usages[len(cpu_usages) - len(stamp_begin_with_first_0):] # match the length
            plt.plot(stamp_begin_with_first_0, cpu_usages, label=csv_name)
        plt.xlabel('seconds')
        plt.ylabel(cpu_usage_str)
        plt.xlim(stamp_begin_with_first_0[0], stamp_begin_with_first_0[-1])
        ylim = 100
        max_y = max(data[csv_names[0]]['cpu_percent'])
        for csv_name in csv_names:
            max_cur = max(data[csv_name]['cpu_percent'])
            max_y = max_cur if max_y < max_cur else max_y
        while ylim < max_y:
            ylim += 100
        plt.ylim(0, ylim)
        #plt.legend(loc='upper right')
        plt.savefig(target_dir + 'Cpu_Usage.png')

        # plot memory usages in GB
        print('draw every_process memory usage in GB...'.format(csv_name))
        plt.clf()
        for csv_name in csv_names:
            stamp_begin_with_first_0 = [stamp - first_start_time for stamp in data[csv_name]['stamp']
                                        if first_start_time <= stamp <= first_end_time]
            memory_gbs = [memory_gb for memory_gb in data[csv_name]['memory_GB']]
            memory_gbs = memory_gbs[len(memory_gbs) - len(stamp_begin_with_first_0):]
            plt.plot(stamp_begin_with_first_0, memory_gbs, label=csv_name)
        plt.xlabel('seconds')
        plt.ylabel(memory_usage_gb_str)
        plt.legend(loc='upper right')
        plt.savefig(target_dir + 'Memory_Usage_GB.png')

        # plot memory usages in GB
        print('draw every_process memory usage in percent...'.format(csv_name))
        plt.clf()
        for csv_name in csv_names:
            stamp_begin_with_first_0 = [stamp - first_start_time for stamp in data[csv_name]['stamp']
                                        if first_start_time <= stamp <= first_end_time]
            memory_percents = [memory_percent for memory_percent in data[csv_name]['memory_percent']]
            memory_percents = memory_percents[len(memory_percents) - len(stamp_begin_with_first_0):]
            plt.plot(stamp_begin_with_first_0, memory_percents, label=csv_name)
        plt.xlabel('seconds')
        plt.ylabel(memory_usage_percent_str)
        plt.legend(loc='upper right')
        plt.savefig(target_dir + 'Memory_Usage_percent.png')


def sigint_handler(sig, frame):
    global process_monitor
    if process_monitor.save_ok():
        process_monitor.save_csv()
        process_monitor.save_plots()
        print('flush done in sigint_handler')

    print('terminate in sigint_handler...')
    sys.exit(TW_EXIT_CODE)

def save_process_info():
    global process_monitor
    global sigint_captured

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

    if process_monitor.save_ok():
        process_monitor.save_csv()
        process_monitor.save_plots()

    #sys.exit(TW_EXIT_CODE)

if __name__=='__main__':
    parser = argparse.ArgumentParser(description='Simple Process cpu & memory tracker')
    parser.add_argument('--dir-name', type=str,
                        help='name of result folder')
    parser.add_argument('--plot-only', type=bool,
                        help='if you only want to plot with csv, set this to True')
    parser.add_argument('--plot-csvdir', type=str,
                        help='name of csv-saved folder')
    args = parser.parse_args()

    if args.plot_only and args.plot_csvdir is None:
        print('you must set --plot-csvdir when you use plot-only')
        sys.exit(-1)

    ## plot-only handling
    if args.plot_only:
        process_monitor = ProcessMonitor(proc_names.exe_names, args.plot_csvdir)
        process_monitor.save_plots()
        sys.exit(TW_EXIT_CODE)
        print('after TW_EXIT')

    process_monitor = ProcessMonitor(proc_names.exe_names, args.dir_name)

    # set sigint handler for ctrl+C
    signal.signal(signal.SIGINT, sigint_handler)

    save_process_info()
    sys.exit(TW_EXIT_CODE)
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