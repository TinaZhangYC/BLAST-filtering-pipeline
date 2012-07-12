# -*- coding: utf-8 -*-
# v.112211

# Copyright (C) 2011, Marine Biological Laboratory
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation; either version 2 of the License, or (at your option)
# any later version.
#
# Please read the docs/COPYING file.

import os
import sys
import numpy

sys.path.append('/'.join(os.path.abspath(__file__).split('/')[:-3]))
try:
    import pipeline.utils.utils
    pp = pipeline.utils.utils.pp
except:
    pp = lambda x: x


QUERY_ID, SUBJECT_ID, IDENTITY, ALIGNMENT_LENGTH,\
MISMATCHES, GAPS, Q_START, Q_END, S_START, S_END,\
E_VALUE, BIT_SCORE = range(0, 12)


class B6Source:
    def __init__(self, b6_source, lazy_init = True):
        self.init()
       
        self.b6_source = b6_source
        self.file_pointer = open(self.b6_source)
        self.file_pointer.seek(0)
        
        self.conversion = [str, str, float, int, int, int, int, int, int, int, float, float]
        
        if lazy_init:
            self.total_seq = None
        else:
            self.total_seq = len([l for l in self.file_pointer.readlines() if not l.startswith('#')])

    def init(self):
        self.pos = 0
        self.entry = None
        self.matrix = []

        #b6 columns..
        self.query_id = None
        self.subject_id = None
        self.identity = None
        self.alignment_length = None
        self.mismatches = None
        self.gaps = None
        self.q_start = None
        self.q_end = None
        self.s_start = None
        self.s_end = None
        self.e_value = None
        self.bit_score = None

    def show_progress(self, end = False):
        sys.stderr.write('\r[b6lib] Reading: %s' % (pp(self.pos)))
        sys.stderr.flush()
        if end:
            sys.stderr.write('\n')

    def next(self, raw = False, show_progress = False, progress_step = 10000):
        while 1:
            self.entry = self.file_pointer.readline()
            
            if self.entry == '':
                if show_progress:
                    self.show_progress(end = True)
                return False

            self.entry = self.entry.strip()
            
            if not (self.entry.startswith('#') or len(self.entry) == 0):
                self.pos   += 1
                break

        if show_progress and (self.pos == 1 or self.pos % progress_step == 0):
            self.show_progress()

        if raw == True:
            return True
      
        try:
            self.query_id, self.subject_id, self.identity, self.alignment_length,\
            self.mismatches, self.gaps, self.q_start, self.q_end, self.s_start,\
            self.s_end, self.e_value, self.bit_score =\
                [self.conversion[x](self.entry.split('\t')[x]) for x in range(0, 12)]
        except:
            print
            print 'Error: There is something wrong with this entry in the B6 file'
            print self.entry
            sys.exit()

        self.entry += '\n'
        return True

    def reset(self):
        self.init()
        self.file_pointer.seek(0)


    def load_b6_matrix(self):
        for i in range(0, 12):
            self.matrix.append([])
        
        F = lambda x, i: self.conversion[i](x)
   
        while self.next(raw = True): 
            if self.pos % 10000 == 0 or self.pos == 1:
                sys.stderr.write('\r[b6_matrix] Reading: %s' % (pp(self.pos)))
                sys.stderr.flush()
 
            b6_columns = self.entry.split(('\t'))
            for i in range(0, 12):
                self.matrix[i].append(F(b6_columns[i], i))

        sys.stderr.write('\n')
        return True
        

    def print_b6_file_stats(self):
        if self.matrix == []:
            self.load_b6_matrix()

        TABULAR = lambda x, y: sys.stdout.write('%s %s: %s\n' % (x, '.' * (20 - len(x)), y))
        INFO    = lambda x: '%-10.2f %-10.2f %-10.2f %-10.2f'\
                                 % (numpy.mean(self.matrix[x]),
                                     numpy.std(self.matrix[x]),
                                     numpy.min(self.matrix[x]),
                                     numpy.max(self.matrix[x]))
     
        print
        TABULAR('Total Hits', pp(len(self.matrix[IDENTITY])))
        print
        print '                        mean       std         min         max'
        print
        TABULAR('Identity', INFO(IDENTITY))
        TABULAR('Alignment Length', INFO(ALIGNMENT_LENGTH))
        TABULAR('Mismatches', INFO(MISMATCHES))
        TABULAR('Gaps', INFO(GAPS))
        TABULAR('Query Start', INFO(Q_START))
        TABULAR('Query End', INFO(Q_END))
        TABULAR('Target Start', INFO(S_START))
        TABULAR('Target End', INFO(S_END))
        TABULAR('E-Value', INFO(E_VALUE))
        TABULAR('Bit Score', INFO(BIT_SCORE))
        print
 
    def visualize_b6_output(self, title_hint, Q_LENGTH = 101):
        if self.matrix == []:
            self.load_b6_matrix()

        import matplotlib.pyplot as plt
        import matplotlib.gridspec as gridspec
 
        def _setp(b, c = 'red'):
            plt.setp(b['medians'], color=c)
            plt.setp(b['whiskers'], color='black', alpha=0.6)
            plt.setp(b['boxes'], color='black', alpha=0.8)
            plt.setp(b['caps'], color='black', alpha=0.6)
            plt.setp(b['fliers'], color='#EEEEEE', alpha=0.01)
    
        fig = plt.figure(figsize = (24, 12))
        plt.rcParams.update({'axes.linewidth' : 0.9})
        plt.rc('grid', color='0.50', linestyle='-', linewidth=0.1)
        
        gs = gridspec.GridSpec(2, 19)
    
        #
        # UPPER PANEL, Q_START AND Q_END
        #
    
        ax1 = plt.subplot(gs[0:15])
        plt.grid(True)
        
        plt.subplots_adjust(left=0.03, bottom = 0.05, top = 0.92, right = 0.97)
     
        plt.title('Alignment Start / End Positions for "%s" (Number of Hits: %s)'\
              % (os.path.basename(self.b6_source) if not title_hint else title_hint, pp(len(self.matrix[0]))))
    
        p1 = [0] * Q_LENGTH
        p2 = [0] * Q_LENGTH
    
        for i in self.matrix[Q_START]:
            p1[i - 1] += 1
        for i in self.matrix[Q_END]:
            p2[i - 1] += 1
        
        p1 = [x * 100.0 / sum(p1) for x in p1]
        p2 = [x * 100.0 / sum(p2) for x in p2]
    
        for i in range(0, len(p1)):
            plt.bar([i], [100], color='green', alpha = (p1[i] / max(p1)) * 0.8, width = 1, edgecolor='green')
        for i in range(0, len(p2)):
            plt.bar([i], [100], color='purple', alpha = (p2[i] / max(p2)) * 0.8, width = 1, linewidth = 0)
    
        ax1.plot(p1, c = 'black', linewidth = 3)
        ax1.plot(p1, c = 'green', label = 'Alignment Start Position')
        ax1.plot(p2, c = 'black', linewidth = 3)
        ax1.plot(p2, c = 'red', label = 'Alignment End Position')
        plt.fill_between(range(0, len(p1)), p1, y2 = 0, color = 'black', alpha = 0.5)
        plt.fill_between(range(0, len(p2)), p2, y2 = 0, color = 'black', alpha = 0.5)
        
        plt.ylabel('Percent of Hits')
        plt.xlabel('Position')
        plt.xticks(range(0, Q_LENGTH, Q_LENGTH / 100), range(1, Q_LENGTH + 1, Q_LENGTH / 100), rotation=90, size='xx-small')
        plt.yticks([t for t in range(0, 101, 10)], ['%s%%' % t for t in range(0, 101, 10)], size='xx-small')
        plt.ylim(ymin = 0, ymax = 100)
        plt.xlim(xmin = 0, xmax = Q_LENGTH - 1)
    
        plt.legend()   
   

        #UPPER PANEL RIGHT SIDE
    
        ax1b = plt.subplot(gs[16:19])
        plt.title('Percent Identity Breakdown')
        
        plt.grid(True)
        percent_brake_down = []
        for p in range(90, 101):
            percent_brake_down.append(len([True for x in self.matrix[IDENTITY] if x >= p]) * 100.0 / len(self.matrix[IDENTITY]))
    
        percent_differences = []
        for i in range(0, len(percent_brake_down)):
            if i < len(percent_brake_down) - 1:
                percent_differences.append(percent_brake_down[i] - percent_brake_down[i + 1])
            else:
                percent_differences.append(percent_brake_down[i])
        percent_differences.sort(reverse = True)
   

        ax1b.bar([t + .05 for t in range(0, 11)], percent_differences, width = .9, color = 'orange')
        plt.xlim(xmax = 11)
        plt.ylim(ymax = 100, ymin = 0)
        plt.xticks([t + .5 for t in range(0, 11)], ['%s%%' % t for t in range(100, 89, -1)], rotation=90, size='xx-small')
        plt.yticks([t for t in range(0, 101, 10)], ['%s%%' % t for t in range(0, 101, 10)], size='xx-small')
        plt.xlabel('Percent Identity Level')
        plt.ylabel('Percent of Hits')
    
        # BOX 1
        ax2 = plt.subplot(gs[19:22])
        plt.grid(True)
        plt.title('Query Alignment Start / End Positions') 
        plt.ylabel('Position in Query')
        b2 = ax2.boxplot([self.matrix[Q_START], self.matrix[Q_END]], positions=[0.5, 1.5], sym=',', widths=0.7)
        _setp(b2)
        plt.xticks([0.5, 1.5], ['Start', 'End'])
        plt.ylim(ymax = 101)
    
        # BOX 2
        ax3 = plt.subplot(gs[23:26])
        plt.grid(True)
        plt.title('Target Alignment Start / End Positions') 
        plt.ylabel('Position in Target')
        b3 = ax3.boxplot([self.matrix[S_START], self.matrix[S_END]], positions=[0.5, 1.5], sym=',', widths=0.7)
        _setp(b3)
        plt.xticks([0.5, 1.5], ['Start', 'End'])
    
    
        # BOX 3
        ax4 = plt.subplot(gs[27:29])
        plt.grid(True)
        plt.title('Percent Identity to Target') 
        plt.ylabel('Percent')
        b4 = ax4.boxplot(self.matrix[IDENTITY], positions=[0.5], sym=',', widths=0.7)
        _setp(b4, 'purple')
        plt.xticks([0.5], [])
        plt.ylim(ymax = 101, ymin = 0)
        
    
        # BOX 4
        ax5 = plt.subplot(gs[30:32])
        plt.grid(True)
        plt.title('Alignment Length') 
        plt.ylabel('Nucleotide')
        b5 = ax5.boxplot(self.matrix[ALIGNMENT_LENGTH], positions=[0.5], sym=',', widths=0.7)
        _setp(b5, 'orange')
        plt.xticks([0.5], [])
        plt.ylim(ymax = 101, ymin = 0)
     
        # BOX 5
        ax6 = plt.subplot(gs[33:35])
        plt.grid(True)
        plt.title('Mismatches and Gaps') 
        plt.ylabel('Number')
        b6 = ax6.boxplot([self.matrix[MISMATCHES], self.matrix[GAPS]], positions=[0.5, 1.5], sym=',', widths=0.7)
        _setp(b6, 'brown')
        plt.xticks([0.5, 1.5], ['Mismatches', 'Gaps'])
    
        # BOX 6
        ax7 = plt.subplot(gs[36:38])
        plt.grid(True)
        plt.title('Bit Score') 
        b7 = ax7.boxplot(self.matrix[BIT_SCORE], positions=[0.5], sym=',', widths=0.7)
        _setp(b7, 'green')
        plt.xticks([0.5], [])
    
 
        try:
            plt.savefig(self.b6_source + '.tiff')
        except:
            plt.savefig(self.b6_source + '.png')

        try:
            plt.show()
        except:
            pass

        return

if __name__ == '__main__':
    b6_f_name = sys.argv[1] 
    b6 = B6Source(b6_f_name)
    b6.visualize_b6_output(sys.argv[2] if len(sys.argv) == 3 else None)
    b6.print_b6_file_stats()
