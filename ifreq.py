#!/usr/bin/python -tt
#
# This script is an attempt to make the contents of /proc/interrupts more eye candy.
# When there are more than 8 CPUs and hundreds of active interrupts,
# output from 'cat /proc/interrupts' become jumbled and becomes hard to decode.
# Wider monitors are the new norm, so why not display the /proc/interrupts
# in landscape mode?.
#
# ifreq.py displays the interrupt's frequency in a ncurses window and uses the below keys
# t -> sort the interrupts based on total occurence
# f -> sort the interrupts based on frequency. aka, itop
# n -> don't sort. Display /proc/interrupts as it it
# Home -> move to the beginning of display
# End -> move to the end of display
# Right arrow -> move the display right by one column
# Left arrow -> move the display left by one column
# q -> quit

import curses
import time
from itertools import islice

ncpu = 0
GOTO_START=0
GOTO_END=1
STAY=-1

NO_SORT=0
FREQ_SORT=1
TOTAL_CNT_SORT=2

def display_help(scr):
    scr.timeout(-1)
    scr.erase()
    scr.addstr(0, 0, "Display the interrupt frequency", curses.A_UNDERLINE)
    scr.addstr(1, 0, "Press the below keys to alter the output")
    scr.addstr(2, 0, "  t: sort based on total interrupt count")
    scr.addstr(3, 0, "  f: sort based on frequency")
    scr.addstr(4, 0, "  n: cancel the sort")
    scr.addstr(5, 0, "  Home: goto beggining of display")
    scr.addstr(6, 0, "  End: goto end of display")
    scr.addstr(7, 0, "  Right arrow: move to right by one column")
    scr.addstr(8, 0, "  Left arrow: move to left by one column")
    scr.addstr(9, 0, "  h: display this message")
    scr.addstr(10, 0, "  q: quit")
    scr.getch()
    scr.timeout(0)


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
        if temp >= col_width:
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

def get_print_start_idx(d, d_len, wl):
    max_width = 0
    print_start_pos = 0
    for idx in range(d_len):
        if ((6 + max_width + d[-(idx+1)]["col_width"]) < wl[1]):
            max_width = max_width + d[-(idx+1)]["col_width"]
        else:
            print_start_pos = d_len - idx
            break

    return print_start_pos


cur_pos=0
def display_data(scr, d, left_or_right, start_or_end):
    global cur_pos
    scr.erase()
    wl = scr.getmaxyx()

    d_len = len(d)

    if left_or_right == 1:
        print_start = get_print_start_idx(d, d_len, wl)
        if cur_pos < print_start:
            cur_pos = cur_pos + 1

    if left_or_right == -1:
        if cur_pos > 0:
            cur_pos = cur_pos - 1

    if start_or_end == GOTO_START:
        cur_pos = 0

    if start_or_end == GOTO_END:
        cur_pos = get_print_start_idx(d, d_len, wl)

    for idx in range(ncpu):
        scr.addstr(idx+1, 0, "{:>6}".format("CPU%d:" % (idx)))

    scr.addstr(idx+2, 0, 'Total:')

    if cur_pos != 0:
        d = islice(d, cur_pos, d_len)

    y = 6
    for int_l in d:
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

    screen.timeout(0)
    sort = NO_SORT
    while True:
        screen.refresh()
        time.sleep(1)
        data2 = collect_int_stats()
        data2 = process_int_stats(data2)
        data_diff = calculate_diff_and_parse(data1, data2)
        data1 = data2

        if sort == FREQ_SORT:
            sort_data = sorted(data_diff, key=lambda k: k['change'], reverse=True)
            data_diff = sort_data

        if sort == TOTAL_CNT_SORT:
            sort_data = sorted(data_diff, key=lambda k: k['total'], reverse=True)
            data_diff = sort_data

        display_data(screen, data_diff, 0, STAY)

        while True:
            c = screen.getch()

            if c == 113:
                exit()  # q
            elif c == 102: # f
                sort = FREQ_SORT
            elif c == 116: # t
                sort = TOTAL_CNT_SORT
            elif c == 110: # n
                sort = NO_SORT
            elif c == 104: # h
                display_help(screen)
            elif c == curses.KEY_RIGHT:
                display_data(screen, data_diff, 1, STAY)
            elif c == curses.KEY_LEFT:
                display_data(screen, data_diff, -1, STAY)
            elif c == curses.KEY_HOME:
                display_data(screen, data_diff, 0, GOTO_START)
            elif c == curses.KEY_END:
                display_data(screen, data_diff, 0, GOTO_END)
            elif c == -1:
                break


try:
    curses.wrapper(main)

except KeyboardInterrupt:
    print "Got KeyboardInterrupt exception. Exiting..."
    exit()
