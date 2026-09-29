"""
Shared name corrections so player names match across data sources

Author: Kevin Kang
"""

import unicodedata
from rapidfuzz import fuzz, process

# Dictionary of name mappings (e.g., nicknames or slight variations)
name_corrections = {
    'Mitch Marner': 'Mitchell Marner',
    'John (Jack) Roslovic': 'Jack Roslovic',
    'Alexander Wennberg': 'Alex Wennberg',
    'Cameron Atkinson': 'Cam Atkinson',
    'Janis Moser': 'J.J. Moser',
    'Patrick Maroon': 'Pat Maroon',
    'Jani Hakanp\x1a§\x1a§': 'Jani Hakanpää',  # raw nhl.com file contains \x1a control characters
    'Mathew Dumba': 'Matt Dumba',
    'Matthew Grzelcyk': 'Matt Grzelcyk',
    'Joshua Brown': 'Josh Brown',
    'Gustav Lindstrom': 'Gustav Lindström',
    'Joshua Mahura': 'Josh Mahura',
    'Jesse Ylonen': 'Jesse Ylönen',
    'Zachary Sanford': 'Zach Sanford',
    'Jake Lucchini': 'Jacob Lucchini',
    'Matt Benning': 'Matthew Benning',
    'Maxime Lajoie': 'Max Lajoie',
    'Maxime Comtois': 'Max Comtois',
    'Alexander Petrovic': 'Alex Petrovic',
    'Matthew Savoie': 'Matt Savoie',
    # Spotrac spellings reviewed from the fuzzy match candidates
    'John-Jason Peterka': 'JJ Peterka',
    'Daniel Vladar': 'Dan Vladar',
    'T.J. Brodie': 'TJ Brodie',
    'Joseph Anderson': 'Joey Anderson',
    'Alexander Georgiev': 'Alexandar Georgiev',
    'J.T Compher': 'J.T. Compher',
    'Cameron Talbot': 'Cam Talbot',
    'Michael Anderson': 'Mikey Anderson',
    'Mats Zuccarello-Aasen': 'Mats Zuccarello',
    'Samuel Montembeault': 'Sam Montembeault',
    'Alex Carrier': 'Alexandre Carrier',
    'Zachary Jones': 'Zac Jones',
    'Yegor Zamula': 'Egor Zamula',
    'Cameron York': 'Cam York',
    'Phillip Grubauer': 'Philipp Grubauer',
    'William Borgen': 'Will Borgen',
    'Alexei Toropchenko': 'Alexey Toropchenko',
    'Emil Martinsen-Lilleberg': 'Emil Lilleberg',
    'Thomas Wilson': 'Tom Wilson',
    'Gabe Vilardi': 'Gabriel Vilardi',
    'Thomas Novak': 'Tommy Novak',
    'Theodor Blueger': 'Teddy Blueger',
}

# Common first-name variants, mapped to one spelling so both sources agree (e.g. Charles McAvoy -> Charlie McAvoy)
first_name_variants = {
    'charles': 'charlie',
    'zachary': 'zach',
    'alexander': 'alex',
    'joshua': 'josh',
    'matthew': 'matt',
    'nicholas': 'nick',
    'mitchell': 'mitch',
    'jacob': 'jake',
    'christopher': 'chris',
    'michael': 'mike',
}

# Build a matching key from a player name: strip accents, lowercase, and map first-name variants
# (only used for matching; the original display names are kept)
def normalize_name(name):
    name = unicodedata.normalize('NFKD', str(name))
    name = ''.join(char for char in name if not unicodedata.combining(char)).lower().strip()
    first, _, rest = name.partition(' ')
    return f"{first_name_variants.get(first, first)} {rest}".strip()

# Print possible fuzzy matches for unmatched (name, team) pairs so they can be reviewed
# and added to name_corrections by hand - nothing is accepted automatically
def print_fuzzy_candidates(unmatched, candidates, score_cutoff=80, limit=3):
    candidate_keys = [normalize_name(name) for name, team in candidates]
    for name, team in unmatched:
        matches = process.extract(normalize_name(name), candidate_keys, scorer=fuzz.WRatio, score_cutoff=score_cutoff, limit=limit)
        options = ', '.join(f"{candidates[i][0]} ({candidates[i][1]}) {score:.0f}" for _, score, i in matches)
        print(f"  {name} ({team}) -> {options if options else 'no candidates'}")
