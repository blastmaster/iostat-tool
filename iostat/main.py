import argparse
import logging

from .consts import DEVICE_SUBPLOTS
from .consts import PLOT_TYPES, PLOT_TYPE_PLOTTER, PLOT_TYPE_SCATTER
from .consts import SUB_COMMAND_CSV, SUB_COMMAND_MONITOR, SUB_COMMAND_PLOT
from .parser import Parser
from .utils import get_logger
from .utils import parse_datetime

__version__ = '0.1.0'
_DATETIME_FORMAT_HELP = 'yyyymmddHHMISS'

_COMMA = 'comma'
_TAB = 'tab'

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s',
)
log = get_logger()


def figsize_type(s):
    values = s.split(',')
    if len(values) != 2:
        msg = 'set width and height in inches, e.g.) "6.4, 4.8"'
        raise argparse.ArgumentTypeError(msg)
    return tuple(float(i.strip()) for i in values)


def dt_type(s):
    return parse_datetime(s)


def sep_type(s):
    if s == _COMMA:
        return ','
    elif s == _TAB:
        return '\n'
    else:
        raise argparse.ArgumentTypeError('separator is wrong')


def parse_csv_argument(subparsers):
    csv_parser = subparsers.add_parser(SUB_COMMAND_CSV)
    csv_parser.set_defaults(
        separator=',',
    )
    csv_parser.add_argument(
        '--separator', action='store', choices=[_COMMA, _TAB],
        help='set separator'
    )


def parse_monitor_argument(subparsers):
    monitor_parser = subparsers.add_parser(SUB_COMMAND_MONITOR)
    monitor_parser.set_defaults(
        iostat_args='',
        max_queue_size=256,
    )
    monitor_parser.add_argument(
        '--iostat-args', action='store', dest='iostat_args',
        help='set arguments for iostat'
    )
    monitor_parser.add_argument(
        '--max-queue-size', action='store', dest='max_queue_size', type=int,
        help='set queue size to read iostat output'
    )


def parse_plot_argument(subparsers):
    plot_parser = subparsers.add_parser(SUB_COMMAND_PLOT)
    plot_parser.set_defaults(
        plot_type=PLOT_TYPE_PLOTTER,
        subplots=DEVICE_SUBPLOTS,
        vlines=[],
    )

    plot_parser.add_argument(
        '--plot-type', action='store', dest='plot_type', choices=PLOT_TYPES,
        help='set plot type ("%s" by default) ' % PLOT_TYPE_PLOTTER
    )
    plot_parser.add_argument(
        '--subplots', action='store', nargs='+', choices=DEVICE_SUBPLOTS,
        help='set subplots to show'
    )
    plot_parser.add_argument(
        '--vlines', action='store', nargs='+', type=dt_type,
        help='set vertical line, format: %s' % _DATETIME_FORMAT_HELP
    )


def parse_argument():
    parser = argparse.ArgumentParser()
    parser.set_defaults(
        backend='Agg',
        data=None,
        figoutput='iostat.png',
        figsize=None,
        output='iostat.log',
        # filter options
        disks=[],
        since=None,
        until=None,
        subcommand=SUB_COMMAND_MONITOR,
    )

    parser.add_argument(
        '--backend', action='store',
        help='set backend for matplotlib, '
             'use TkAgg to monitor in the foreground',
    )
    parser.add_argument(
        '--data', action='store',
        help='set path to iostat output file',
    )
    parser.add_argument(
        '--fig-output', action='store', dest='figoutput',
        help='set path to save graph'
    )
    parser.add_argument(
        '--fig-size', action='store', dest='figsize', type=figsize_type,
        help='set figure size'
    )
    parser.add_argument(
        '--output', action='store',
        help='set path to save output of iostat',
    )

    # filter options
    parser.add_argument(
        '--disks', action='store', nargs='+',
        help='set disk name in iostat'
    )
    parser.add_argument(
        '--since', action='store', type=dt_type,
        help='set since datetime, format: %s' % _DATETIME_FORMAT_HELP
    )
    parser.add_argument(
        '--until', action='store', type=dt_type,
        help='set until datetime, format: %s' % _DATETIME_FORMAT_HELP
    )

    subparsers = parser.add_subparsers(dest='subcommand')
    subparsers.required = True
    parse_csv_argument(subparsers)
    parse_monitor_argument(subparsers)
    parse_plot_argument(subparsers)

    # for debug
    parser.add_argument(
        '-v', '--verbose', action='store_true',
        help='set verbose mode')
    parser.add_argument(
        '--version', action='version', version='%%(prog)s %s' % __version__,
        help='show program version',
    )

    args = parser.parse_args()
    if args.verbose:
        log.setLevel(logging.DEBUG)

    return args


def main():
    args = parse_argument()
    log.debug(args)

    import matplotlib
    matplotlib.use(args.backend)

    if args.subcommand == SUB_COMMAND_MONITOR:
        from .process import run_iostat
        run_iostat(args)
    else:
        if args.data is None:
            log.error('set target file with "--data path/to/file"')
            return

        parser = Parser(args)
        stats = [stat for stat in parser.parse()]

        if args.subcommand == SUB_COMMAND_CSV:
            print('to be implemented')
        elif args.subcommand == SUB_COMMAND_PLOT:
            if args.plot_type == PLOT_TYPE_PLOTTER:
                from .plotter import Plotter
                plotter = Plotter(args, stats)
                plotter.plot()
                plotter.render()
            elif args.plot_type == PLOT_TYPE_SCATTER:
                from .scatter import Scatter
                scatter = Scatter(args)
                for stat in stats:
                    scatter.scatter(stat)
                scatter.render()


if __name__ == '__main__':
    main()
