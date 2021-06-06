import gpustat
from gpustat import core
import sys

'''
most of the impl. is from https://github.com/wookayin/gpustat/blob/master/gpustat/core.py
'''

def print_gpustat(json=False, debug=False, **kwargs):
    '''
    Display the GPU query results into standard output.
    '''
    try:
        gpu_stats = core.GPUStatCollection.new_query()
    except Exception as e:
        sys.stderr.write('Error on querying NVIDIA devices.'
                         ' Use --debug flag for details\n')
        if debug:
            try:
                import traceback
                traceback.print_exc(file=sys.stderr)
            except Exception:
                # NVMLError can't be processed by traceback:
                #   https://bugs.python.org/issue28603
                # as a workaround, simply re-throw the exception
                raise e
        sys.exit(1)

    if json:
        gpu_stats.print_json(sys.stdout)
    else:
        gpu_stats.print_formatted(sys.stdout, **kwargs)


if __name__ == '__main__':
    print_gpustat(show_header=False)