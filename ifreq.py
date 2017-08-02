#!/usr/bin/python -tt

import curses
import time
from itertools import islice

ncpu = 0

# dict = {id= col0, count = (1,2,3 ...) , name = "str"}

def collect_int_stats():
    path = "/proc/interrupts"
    fop = open(path, "r")
    data = fop.readlines()
    fop.close()
    return data


def count_cpus():
    global ncpu
    data = collect_int_stats()[0]
    ncpu = len(data.split())


def process_int_stats(data):
    ret_list = []
    #Skipp line1, it contains CPU names
    for line in islice(data, 1, None):
        line = line.split()
        int_stat = []
        int_name = ''
        int_id = line[0]

        for i in range(1, ncpu + 1):
            if i < len(line):
                int_stat.append(int(line[i]))

        for name in islice(line, ncpu + 1, None):
            if not int_name:
                int_name += name
            else:
                int_name += ' '
                int_name += name

        int_info = {
                'id' : int_id,
                'counts' : int_stat,
                'name' : int_name
        }

        ret_list.append(int_info)

    return ret_list


def calculate_diff_and_parse(d1, d2):
    ret_list = []

    for idx in range(len(d1)):
        int1 = d1[idx]
        int2 = d2[idx]
        diff_cnt = []

        int1_cnt = int1["counts"]
        int2_cnt = int2["counts"]

        total_cnt = 0

        #Five is the max default width required to print the int of type LOC:
        col_width = 5
        change = 0
        for idx_cnt in range(len(int1_cnt)):
            diff = int2_cnt[idx_cnt] - int1_cnt[idx_cnt]
            change = change + diff
            diff_cnt.append(diff)
            total_cnt = total_cnt + int2_cnt[idx_cnt]
            temp = len(str(diff))
            if temp > col_width:
                col_width = temp

        temp = len(str(total_cnt))
        if temp > col_width:
            col_width = temp + 1

        int_diff = {
                'id' : int1["id"],
                'counts' : diff_cnt,
                'name' : int1["name"],
                'total' : total_cnt,
                'change' : change,
                'col_width' : col_width
        }

        ret_list.append(int_diff)

    return ret_list

start = 0
def display_data(d, scr):
    global start
    scr.erase()
    xy = scr.getbegyx()
    wl = scr.getmaxyx()
    #scr.addstr("xy%s wl%s" % (str(xy), str(wl)))

    scr.timeout(0)

    c = scr.getch()
    if c == 113: exit()  # q
    elif c == curses.KEY_RIGHT:
        start = start + 1
    elif c == curses.KEY_LEFT:
        if start != 0:
            start = start - 1
    elif c == curses.KEY_HOME:
        start = 0
    elif c == curses.KEY_END:
        start = len(d) - 10

    for idx in range(ncpu):
        scr.addstr(idx+1, 0, "{:>6}".format("CPU%d:" % (idx)))

    scr.addstr(idx+2, 0, 'Total:')

    newd = sorted(d, key=lambda k: k['change'], reverse=True)
    #newd = sorted(d, key=lambda k: k['change'])

    y = 6
    if start != 0:
        newd = islice(newd, start, len(newd))

    for int_l in newd:
        col_w = int_l["col_width"]

        if (y + col_w) > wl[1]:
            break

        scr.addstr(0, y, ("{:>%d}" % (col_w)).format("%s" % int_l["id"]))
        int_cnt = int_l["counts"]
        for idx in range(len(int_cnt)):
            scr.addstr(idx+1, y, ("{:>%d}" % (col_w)).format("%d" % (int_cnt[idx])))
        scr.addstr(idx+2, y, ("{:>%d}" % (col_w)).format("%d" % (int_l["total"])))
        y=y+col_w


def main(screen):
    curses.use_default_colors()
    screen.scrollok(1)
    count_cpus()

    data1 = collect_int_stats()
    data1 = process_int_stats(data1)
    while True:
        screen.refresh()
        time.sleep(1)
        data2 = collect_int_stats()
        data2 = process_int_stats(data2)
        data_diff = calculate_diff_and_parse(data1, data2)
        display_data(data_diff, screen)
        data1 = data2

try:
    curses.wrapper(main)

except KeyboardInterrupt:
    print "Got KeyboardInterrupt exception. Exiting..."
    exit()
