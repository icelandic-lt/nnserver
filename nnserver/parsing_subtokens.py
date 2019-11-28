#!/usr/bin/env python

"""
    Reynir: Natural language processing for Icelandic

    Parsing Subtokens

    Copyright (C) 2018 Miðeind

       This program is free software: you can redistribute it and/or modify
       it under the terms of the GNU General Public License as published by
       the Free Software Foundation, either version 3 of the License, or
       (at your option) any later version.
       This program is distributed in the hope that it will be useful,
       but WITHOUT ANY WARRANTY; without even the implied warranty of
       MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
       GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see http://www.gnu.org/licenses/.


    This module defines composite parsing tokens for Icelandic intended to
    be used as for subword encoding of flattened parse trees.

"""

from nnserver import _PARSING_VOCAB

UNK = "<UNK>"
MISSING = ["NP-AGE", "ADVP-DUR"]
MISSING.extend(["/" + t for t in MISSING])
MISSING = set(t for t in MISSING)


def _preprocess_word_v1(word):
    return (
        word.strip()
        .replace("_lh_nt", "_lhnt")
        .replace("_hvk", "_hk")
        .replace("_hk_hk", "_hk")
    )


def _preprocess_word_v2(word):
    return word.strip().replace("_lhþt", "_lh_þt")


class ParsingSubtokens:
    """ Definition for composite parsing tokens made from
        Greynir's flattened parse trees, to be used as part
    of a subword encoder. """

    def __init__(self, path=None, version=1):
        self.version = version

        if path is None:
            path = _PARSING_VOCAB

        with open(path, "r") as file:
            all_tokens = [self.preprocess_word(l) for l in file.readlines()]

        full_toks = {t for t in all_tokens if "_" not in t}
        raw_tokens = {t for t in all_tokens if "_" in t}

        head_toks = set()
        tail_toks = set()
        for rt in raw_tokens:
            toks = rt.split("_")
            head, t1 = toks[:2]
            tail = toks[2:]

            if t1 in ["0", "1", "2", "subj"]:
                head = head + "_" + t1
            else:
                tail.append(t1)

            tail_toks.update(tail)
            head_toks.add(head)

        self.NONTERMINALS = {t for t in all_tokens if t == t.upper()}
        self.NONTERM_L = {t for t in self.NONTERMINALS if "/" not in t}
        self.NONTERM_R = self.NONTERMINALS - self.NONTERM_L
        self.TERMINALS = (head_toks | full_toks | tail_toks) - self.NONTERMINALS
        self.R_TO_L = {"/" + t: t for t in self.NONTERM_L}

        full_toks = sorted(full_toks)
        head_toks = sorted(head_toks)
        tail_toks = sorted(tail_toks)

        self._tok_id_to_tok_str = {
            tid: tok
            for (tid, tok) in enumerate(
                full_toks + head_toks + [("_" + t) for t in tail_toks] + [UNK]
            )
        }

        N_FULL, N_HEAD, N_TAIL = [len(s) for s in [full_toks, head_toks, tail_toks]]

        self._ftok_to_tok_id = {tok: i for (i, tok) in enumerate(full_toks)}
        self._htok_to_tok_id = {tok: (i + N_FULL) for (i, tok) in enumerate(head_toks)}
        self._ttok_to_tok_id = {
            tok: (i + N_FULL + N_HEAD) for (i, tok) in enumerate(tail_toks)
        }
        self.oov_id = N_FULL + N_HEAD + N_TAIL

    def preprocess_word(self, word):
        if self.version == 1:
            return _preprocess_word_v1(word)
        return _preprocess_word_v2(word)
