## This program should run with root previlege, depending on your cmd
## this program uses memory with linear increasing speed.

import ps_tool
import os
import threading
import time

PROCESS_UPDATE_PERIOD = 1 # second
exe_names = [ #you can write node_name when you use ROS
    'run_subscribe_msckf',
    'move_base',
]


class ProcessMonitor:
    def __init__(self, exe_names):
        self.p_infos = [ps_tool.ProcessLogger(exe_name) for exe_name in exe_names]

    def trackProcess(self, pid):
        self.p_infos.append(ProcessMonitor.ProcessInfo(pid))

    def update(self):
        for p_info in self.p_infos:
            if p_info.found:
                if not p_info.terminated:
                    p_info.logCpuMemory()
            else: # not found
                pid = p_info.searchProc()
                if pid != -1:
                    p_info.doInit(pid)


def updateProcessInfo():
    global process_monitor
    last_time = time.time()
    while True:
        dt = (time.time() - last_time)
        if dt >= PROCESS_UPDATE_PERIOD:
            # update processes
            last_time = time.time()
            process_monitor.update()
        else:
            time.sleep(1/1000.0) #1ms


if __name__=='__main__':
    process_monitor = ProcessMonitor(exe_names)

    # append cpu and memory usage according to the cycle
    thr = threading.Thread(target=updateProcessInfo)
    thr.daemon = True
    thr.start()


    while True:
        time.sleep(1)
        ## sig child...
        ## exit handling...
