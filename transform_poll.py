#!/usr/bin/python3
# transform_poll.py
# Takes a text (pipe-separated) dump from nextcloud oc_polls_votes
# (filtered for the correct poll_id) and transforms it to a 2D table
# output as pipe-separated text again (to stdout).
#
# (c) Kurt Garloff <garloff@osb-alliance.com>, 1/2022
# SPDX-License-Identifier: AGPL-3.0

import sys, getopt

def ws_strip(stg):
    "Remove whitespace left and right"
    return stg.strip(' ').rstrip(' ')

class PollLn:
    "Class to hold the database lines from nextcloud date polls"
    def __init__(self, txt):
        "Constructure that parses a text pipe-separated database line"
        fields = txt.split("|")
        (self.id, self.poll_id, self.user_id, self.vote_option_id, 
         self.vote_option_text, self.vote_answer) = \
        (int(fields[0]), int(fields[1]), ws_strip(fields[2]),
         int(fields[3]), ws_strip(fields[4]), ws_strip(fields[5]))

def read_tbl(f):
    "Read all lines from text file f, fill db lines and return"
    lines = []
    for ln in f:
        if ln == "\n":
            continue
        lines.append(PollLn(ln.rstrip("\n")))
    return lines

class VoteRes:
    "Data structure that holds all the votes for one voter"
    def __init__(self, voter, nr_opts, opt_idx, opt_vote):
        "Create object for voter with nr_opts options and vote opt_vote for option nr opt_idx"
        self.voter = voter
        self.nr_opts = nr_opts
        self.votes = [""] * nr_opts
        assert(opt_idx < nr_opts)
        self.votes[opt_idx] = opt_vote
    def set(self, opt_idx, opt_vote):
        "Set vote for vote opt for option optidx"
        assert(opt_idx < self.nr_opts)
        self.votes[opt_idx] = opt_vote
    def __str__(self):
        "Output pipe seperated line with all votes for voter"
        stg = self.voter
        for i in range(0, self.nr_opts):
            stg += ' | ' + self.votes[i]
        return stg

# Global setting whether to transform votes into numbers
do_out_numbers = False

# Options and default numbers
vote_strs = ("yes", "maybe", "", "no")
vote_vals = [1.0, 0.4, 0, -0.1]

def vote2num(vote_text, transform=False):
    "Transform votes to numbers"
    if not transform:
        return vote_text
    else:
        for opt in range(0, len(vote_strs)):
            if vote_text == vote_strs[opt]:
                return vote_vals[opt]
        raise ValueError(stg)

class Tbl:
    "Data structure to hold a table of all voters and votes"
    def find_vote(self, voter):
        "Return vote if voter is in the list already, None otherwise"
        for v in self.votes:
            if v.voter == voter:
                return v
        return None

    def __init__(self, db_lns):
        "Create table from all vote records in db_lns, also text for options"
        self.votes = []
        min_opt = min(map(lambda x: x.vote_option_id, db_lns))
        max_opt = max(map(lambda x: x.vote_option_id, db_lns))
        #print("Options range from %i to %i" % (min_opt, max_opt), file=sys.stderr)
        self.nr_opts = max_opt+1 - min_opt
        self.opts = [None]*self.nr_opts
        for db_ln in db_lns:
            vote_id = db_ln.vote_option_id - min_opt
            vote = self.find_vote(db_ln.user_id)
            assert(vote_id < self.nr_opts)
            if vote:
                vote.set(vote_id, db_ln.vote_answer)
            else:
                self.votes.append(VoteRes(db_ln.user_id, self.nr_opts, vote_id, db_ln.vote_answer))
            if not self.opts[vote_id]:
                self.opts[vote_id] = db_ln.vote_option_text

    def __str__(self):
        "Output 2D table with all voters and votes"
        global outnum
        # Header
        stg = "#Name"
        for opt_id in range(0, self.nr_opts):
            stg += " | " + self.opts[opt_id]
        # Votes
        for v in self.votes:
            stg += "\n" + v.voter
            for opt_id in range(0, self.nr_opts):
                stg += " | " + str(vote2num(v.votes[opt_id], do_out_numbers))
        return stg

def usage():
    "Help"
    print("Usage: transform_poll.py [-n numbers] [-p poll_id] table", file=sys.stderr)
    print("    Takes polls_vote nextcloud DB export (tab sep text file) and")
    print("    and transforms it to a 2D table (written to stdout)")
    print(" -n assigns numeric values to votes yes, maybe, (empty), no")
    print(" -p instead connects to a database (pass sqlalchemy conn str in table)")
    print("    poll_id selects the poll, 0 lists all polls")
    sys.exit(1)

def main(argv):
    global do_out_numbers, vote_vals
    poll_id = -1
    try:
        opts, args = getopt.gnu_getopt(argv[1:], 'hn:p:', ('help',))
    except getopt.GetoptError as exc:
        print >>sys.stderr, exc
        usage()
    for (opt, arg) in opts:
        if opt == '-h' or opt == '--help':
            usage()
        if opt == "-n":
            do_out_numbers = True
            if arg:
                vote_vals = list(map(lambda x: float(x), arg.split(",")))
        if opt == "-p":
            poll_id = int(arg)

    if not args:
        usage()

    if poll_id == -1:
        poll = Tbl(read_tbl(open(args[0], "r")))
    else:
        import oc_database
        if poll_id == 0:
            sys.exit(oc_database.main((args[0]),))
        poll = Tbl(oc_database.get_votes(args[0], poll_id))
    print("%s" % poll)

if __name__ == "__main__":
    main(sys.argv)
    
