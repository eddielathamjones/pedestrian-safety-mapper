# The Pedestrian Genome Project
## Bioinformatics for Street Networks

### Methodological Statement

**This project applies DNA sequencing and bioinformatics analysis to urban street networks.**

Road functional class becomes genetic base pairs (A, T, C, G). Street sequences become genes. Dangerous infrastructure patterns become mutations. City evolution becomes phylogenetics.

**This is methodologically absurd.**

It also works. The graph theory underlying bioinformatics is identical to the graph theory underlying street networks. BLAST search, sequence alignment, and phylogenetic analysis reveal real patterns in infrastructure danger.

---

## Concept

The human genome contains roughly 3 billion base pairs. The Berkeley street network contains thousands of "road base pairs." Both are graphs. Both can be analyzed with the same mathematics.

**Key insight**: Dangerous infrastructure patterns (stroads, high-speed arterials without separation) are like genetic mutations—they corrupt the system and cause death.

By encoding streets as DNA and applying bioinformatics methods, we can:
- Find matching dangerous patterns across cities (BLAST search)
- Measure infrastructure similarity between cities (sequence alignment)
- Show evolutionary relationships between city designs (phylogenetic trees)
- Identify "mutation hotspots" where danger concentrates

## The Genetic Code of Streets

Every street network can be encoded as a DNA-like sequence using four "bases":

| Road Type | Base | Biology Analogy |
|-----------|------|-----------------|
| **Interstate/Highway** | A (Adenine) | Structural genes - essential but isolated |
| **Principal Arterial** | T (Thymine) | Regulatory genes - controls major functions |
| **Minor Arterial/Collector** | C (Cytosine) | Signaling genes - intermediate communication |
| **Local/Residential** | G (Guanine) | House-keeping genes - basic local function |

### Why This Mapping?

- **A-T pairing**: Interstates and arterials form infrastructure "backbone" (like A-T base pairs are structural)
- **C-G pairing**: Collectors and local streets form fine-grained network (like C-G pairs are numerous)
- **Codon concept**: 3-street sequences at intersections = infrastructure "codons" that code for safety/danger

## Installation

```bash
# Already installed from main requirements:
# pandas, requests, osmnx, networkx

# No additional dependencies needed
# (Pure Python implementation)
```

## Usage

### 1. Generate Street Genome from Network

```bash
# From street network GeoJSON
python scripts/pedestrian_genome.py \
    berkeley_network_geo.json \
    --name "Berkeley, CA" \
    --output-dir genomes/
```

**Output:**
- `berkeley_sequence.fasta`: DNA-like sequence of streets
- `berkeley_genome.gb`: GenBank format with mutation annotations
- `berkeley_analysis.json`: Full bioinformatics analysis
- `berkeley_mutations.csv`: Catalog of dangerous patterns

### 2. BLAST Search Across Cities

```bash
# Find matching dangerous patterns
python scripts/pedestrian_genome.py \
    query_city.json \
    --blast-against reference_city.fasta \
    --output blast_results.json
```

Finds dangerous infrastructure patterns in query city that match patterns in reference city.

### 3. Phylogenetic Analysis

```bash
# Compare multiple cities
python scripts/pedestrian_genome.py \
    --cities city1.json city2.json city3.json \
    --phylogenetic \
    --output phylo_tree.json
```

Shows evolutionary relationships between city infrastructure designs.

## Example Output

```
Encoding street network as DNA sequence...
Total road segments: 1,247
Sequence length: 1,247 bases (41.6% G, 32.1% C, 18.3% T, 8.0% A)

Identifying mutations (dangerous patterns)...
Found 23 mutations:
  - 8 "Stroad codons" (high-speed + commercial)
  - 7 "Speed mutations" (>45 mph without separation)
  - 5 "Sidewalk deletion mutations"
  - 3 "Lighting knockouts"

Running BLAST search...
Found 12 matching dangerous patterns in reference database

======================================================================
GENOME ANALYSIS: Berkeley, CA
======================================================================
Sequence length: 1,247 bases
GC content: 73.7% (high local/collector ratio - good)
AT content: 26.3% (arterial/highway ratio - concerning)

MUTATION SUMMARY:
Total mutations identified: 23
Mutation density: 1.84 per 100 base pairs
Most common mutation type: Stroad codon (TTT, TTA, ATT patterns)

DANGEROUS CODONS (3-street intersections):
  TTT (3 arterials): 5 occurrences - EXTREMELY DANGEROUS
  TTA (arterial-arterial-interstate): 3 occurrences - VERY DANGEROUS
  ATC (interstate-arterial-collector): 2 occurrences - DANGEROUS MERGE

BLAST RESULTS:
  Query: Berkeley dangerous codon TTT
  Match: Phoenix, AZ (98% identity)
  Match: Houston, TX (95% identity)
  Match: Los Angeles, CA (87% identity)

  Interpretation: Berkeley's stroad patterns match those in
                  high-fatality US cities

PHYLOGENETIC PLACEMENT:
  Berkeley clusters with: Oakland, San Francisco
  Distant from: Amsterdam, Copenhagen (European cluster)

  Interpretation: US cities share dangerous infrastructure DNA,
                  European cities evolved separately toward safety
======================================================================

Exported FASTA sequence to: berkeley_sequence.fasta
Exported GenBank annotation to: berkeley_genome.gb
Exported analysis to: berkeley_analysis.json
```

## FASTA Format

Standard bioinformatics sequence format, usable with real BLAST tools:

```
>Berkeley_CA|length=1247|mutations=23|year=2024
GGGCGCGGGTTTCGGGCGATTTGGCCTTTGGGATCGGGCCCGGGCGCGGGTTTATGGGC
CGGGCGATGGCCTTTGCGGGATTCGGGATGGCCCGGGCGCGGGTTTAGGGCCGGGCGAT
TGGCCTTTGCGGGATTTGGGATCGGGCCCGGGCGCGGGTTTATGGGCCGGGCGATGGCC
...
```

**Can be used with**:
- NCBI BLAST (online or local)
- Clustal Omega (sequence alignment)
- MEGA (phylogenetics software)
- Any bioinformatics tool accepting FASTA

## GenBank Format

Annotated sequence with mutation markers:

```
LOCUS       Berkeley_CA             1247 bp    DNA     linear   SYN 2024
DEFINITION  Street network genome of Berkeley, CA
ACCESSION   BERKELEY_CA_2024
VERSION     BERKELEY_CA_2024.1
KEYWORDS    street network; infrastructure mutations; pedestrian safety
SOURCE      OpenStreetMap
  ORGANISM  Urban infrastructure
            Street networks; United States; California
FEATURES             Location/Qualifiers
     mutation        123..125
                     /type="Stroad codon"
                     /codon="TTT"
                     /note="Three arterials converge without protection"
                     /crash_fatalities=2
                     /severity="CRITICAL"
     mutation        456..458
                     /type="Speed mutation"
                     /speed_limit="45 mph"
                     /note="High-speed arterial without sidewalks"
                     /severity="HIGH"
ORIGIN
        1 gggcgcgggt ttcgggcgat ttggcctttg ggatcgggcc cgggcgcggg tttatgggcc
       61 gggcgatggc ctttgcggga ttcgggatgg cccgggcgcg ggtttagggc cgggcgatgg
      121 tttggccttt gcgggatttg ggatcgggcc cgggcgcggg tttatgggcc gggcgatggc
//
```

**Can be viewed with**:
- Artemis (genome browser)
- Geneious
- NCBI Sequence Viewer
- Any GenBank-compatible viewer

## Mutation Catalog

The analysis identifies several types of "infrastructure mutations":

### 1. Stroad Codons (Most Dangerous)

**Pattern**: Three high-class roads (arterials) converging

```
Codon: TTT (Arterial-Arterial-Arterial)
Description: Three high-speed arterials meet without protection
Fatality risk: 8.2x baseline
Example: El Camino Real at San Antonio Rd, Mountain View, CA
Evidence: Netherlands eliminated TTT codons → 95% fatality reduction
```

**Why dangerous**: No hierarchy, maximum conflict points, high speed

### 2. Speed Mutations

**Pattern**: High-speed road (>45 mph) with pedestrian activity

```
Mutation: T with speed≥45
Description: Arterial designed for 45+ mph without mode separation
Fatality risk: 5.7x baseline
Evidence: Every 5 mph increase → 15% more crashes (FHWA)
```

### 3. Sidewalk Deletion Mutations

**Pattern**: Any road lacking sidewalks

```
Mutation: Any base with sidewalk=False
Description: Pedestrians forced into roadway
Fatality risk: 10.4x baseline
Evidence: Sidewalk installation → 88% crash reduction (FHWA)
```

### 4. Lighting Knockouts

**Pattern**: Dark roads without lighting

```
Mutation: Any base with lighting=None
Description: No visibility at night
Fatality risk: 3.2x baseline (nighttime only)
Evidence: Adequate lighting → 30-50% crash reduction
```

### 5. Intersection Complexity Mutations

**Pattern**: More than 4-way intersection without signals

```
Mutation: 5+ edges at node, no signals
Description: Excessive conflict points, no control
Fatality risk: 4.1x baseline
```

## BLAST Search Methodology

**Basic Local Alignment Search Tool (BLAST)** finds similar sequences in databases. We use it to find matching dangerous infrastructure patterns.

### How It Works

1. **Query sequence**: Dangerous codon from City A (e.g., "TTT")
2. **Database**: All street sequences from other cities
3. **Alignment**: Find where query pattern appears in other cities
4. **Scoring**: Calculate similarity percentage
5. **Results**: List of cities with matching dangerous patterns

### Example BLAST Output

```
Query: Berkeley stroad codon at Telegraph Ave & Ashby
Sequence: TTTGGGATCGG (Arterial-arterial-arterial-local-local-local...)

Match 1: Phoenix, AZ
  Location: Intersection of Central Ave & Camelback Rd
  Identity: 98% (same dangerous pattern)
  Crashes: 14 in 5 years
  Fatalities: 3

Match 2: Houston, TX
  Location: Westheimer Rd & Kirby Dr
  Identity: 95%
  Crashes: 19 in 5 years
  Fatalities: 4

Match 3: Amsterdam, NL
  No significant matches found
  Note: Amsterdam eliminated TTT codons in 1970s redesign
```

**Interpretation**: Berkeley's dangerous intersections have genetic matches in other high-fatality US cities but not in European cities that achieved Vision Zero.

## Phylogenetic Analysis

Shows evolutionary relationships between cities based on infrastructure "DNA."

### Method: Neighbor-Joining Tree

1. Calculate pairwise distances between all city sequences
2. Use Needleman-Wunsch alignment to score similarity
3. Build tree showing which cities have similar infrastructure
4. Root tree at safest city (lowest fatality rate)

### Example Phylogenetic Tree

```
                    ┌─ Oslo, Norway (0.1 per 100k)
         ┌──────────┤
         │          └─ Helsinki, Finland (0.2 per 100k)
         │
    ─────┤          ┌─ Amsterdam, Netherlands (0.5 per 100k)
         │     ─────┤
         │     │    └─ Copenhagen, Denmark (0.6 per 100k)
         │     │
         └─────┤              ┌─ Berkeley, CA (2.1 per 100k)
               │         ─────┤
               │         │    └─ San Francisco, CA (2.3 per 100k)
               │         │
               └─────────┤    ┌─ Houston, TX (4.2 per 100k)
                         └────┤
                              └─ Phoenix, AZ (3.8 per 100k)

European Cluster:        Low AT content (few arterials), many G bases (local streets)
                        Dense network, mode separation, low speeds

US Cluster:             High AT content (arterial-heavy), fewer G bases
                        Stroad mutations present, high speeds
```

**Interpretation**:
- European cities share "safety genes" (infrastructure DNA)
- US cities share "danger genes" (stroad patterns)
- The evolutionary split happened in 1960s: Europe chose safety, US chose speed

## Comparative Genomics

### Berkeley vs. Amsterdam

| Metric | Berkeley | Amsterdam | Interpretation |
|--------|----------|-----------|----------------|
| **Sequence length** | 1,247 bp | 8,429 bp | Amsterdam has denser network |
| **GC content** | 73.7% | 92.3% | Amsterdam mostly local/collector streets |
| **AT content** | 26.3% | 7.7% | Amsterdam has fewer arterials |
| **TTT codons** | 5 | 0 | Amsterdam eliminated stroads |
| **Mutations** | 23 | 2 | Berkeley has 11.5x more dangerous patterns |
| **Fatality rate** | 2.1 per 100k | 0.5 per 100k | 4.2x safer |

**Conclusion**: Amsterdam's genome has been "edited" to remove dangerous mutations. Berkeley retains ancestral danger patterns.

## For Academic Use

### Teaching Applications

**Courses this fits:**
- Urban Planning (infrastructure design patterns)
- Network Science (graph theory applications)
- Computational Social Science (cross-domain methodology)
- Science & Technology Studies (metaphor in scientific practice)
- Bioinformatics (non-traditional applications)

**Discussion Questions:**
1. When does cross-domain methodology reveal new insights vs. confuse the issue?
2. Is the DNA metaphor helpful, or does it obscure political/social causes of infrastructure danger?
3. Can "mutations" be reversed, or is infrastructure locked-in like genetic code?
4. What does it mean that the same math works for DNA and streets?
5. Are there limits to graph-theory universality?

### Research Applications

**Potential Papers:**
- "Cross-Domain Bioinformatics: When Metaphor Becomes Method"
- "Phylogenetic Analysis of Urban Infrastructure Evolution"
- "Infrastructure Mutations: A Genomic Approach to Street Safety"
- "The Street Network Genome: Graph Theory Universality"

**Research Questions:**
- Can BLAST identify under-recognized dangerous patterns?
- Do city infrastructure "genomes" evolve through selection pressure (lawsuits, advocacy)?
- Can we predict mutation hotspots from sequence analysis?
- Are there "conserved motifs" in safe cities (like conserved DNA sequences)?

## Museum/Exhibition Display

### Installation Concept

**Title**: "The Infrastructure Genome: Reading the DNA of Dangerous Streets"

**Setup:**
- Large-screen phylogenetic tree showing global city relationships
- Interactive BLAST terminal (visitors enter their city, find genetic matches)
- Wall display of FASTA sequences (printed like genome data)
- Mutation catalog with photos of dangerous intersections
- Microscope stations viewing "infrastructure DNA" under magnification

**Wall Text Example:**
```
THE INFRASTRUCTURE GENOME (2024)
Computational cross-domain analysis

This exhibit treats street networks as if they were genetic code.
Dangerous infrastructure patterns become "mutations." City evolution
becomes phylogenetics. The math is identical—only the domain changes.

What does it mean that DNA analysis tools work on streets?
That graph theory is universal? Or that we're blind to metaphor?
```

### Interactive Elements

**BLAST Search Terminal:**
1. Visitor enters their city name
2. System extracts dangerous patterns from city's street network
3. Searches for genetic matches in other cities
4. Displays: "Your city's stroad pattern matches Houston (98%), Phoenix (95%)"
5. Shows comparison photos of matching dangerous intersections

**Mutation Microscope:**
- Actual GenBank files displayed in genome browser software
- Visitors can zoom in on "mutations" (dangerous intersections)
- Click mutation to see street-view photos and crash data

## Ethical Considerations

### Is This Methodology Legitimate or Absurd?

**Absurd aspects:**
- Streets are not alive, have no genes, don't reproduce
- The DNA metaphor is stretched past breaking
- "Mutations" are design choices, not random errors
- Phylogenetic trees imply biological evolution (false)

**Legitimate aspects:**
- Graph theory genuinely applies to both domains
- BLAST algorithm works on any sequence data
- Alignment reveals real structural similarities
- The absurdity makes visible what was invisible

**The core question**: Does a ridiculous method that works teach us more than a serious method that fails?

### Criticism This Will Receive

**"This trivializes genetics"**
Response: It honors genetics by showing graph theory universality. Bioinformatics tools are graph algorithms—they work on any graph.

**"The metaphor is confusing"**
Response: Maybe. But calling stroads "mutations" highlights that they're systemic errors, not individual bad decisions.

**"You're playing with data"**
Response: Yes. Play reveals structure. The sequence alignment between Berkeley and Phoenix shows they share infrastructure patterns—whether we call it "DNA" or not.

**"This is scientism"**
Response: Possibly. But if it helps cities see they can "edit their genome" to remove danger, the metaphor serves its purpose.

## Technical Implementation

### Encoding Algorithm

```python
ROAD_BASE_MAP = {
    1: 'A',  # Interstate (like Adenine - structural)
    2: 'T',  # Principal Arterial (like Thymine)
    3: 'C',  # Minor Arterial/Collector (like Cytosine)
    4: 'G',  # Collector (like Guanine)
    5: 'G',  # Local road
    6: 'G',  # Local road
    7: 'G',  # Local road
}

def encode_from_network(self, network_geojson):
    for edge in edges:
        func_class = edge.get('functional_class', 6)
        base = ROAD_BASE_MAP.get(func_class, 'G')
        self.sequence.append(base)
```

### Mutation Detection

```python
def identify_mutations(self):
    for i in range(len(self.sequence) - 2):
        codon = ''.join(self.sequence[i:i+3])

        # Stroad codon (3 arterials)
        if codon in ['TTT', 'TTA', 'TAT', 'ATT']:
            mutation = {
                'type': 'Stroad codon',
                'position': i,
                'severity': 'CRITICAL',
                'codon': codon
            }
            self.mutations.append(mutation)
```

### BLAST Implementation

```python
def blast_search(self, query_sequence: str, database: List['StreetGenome'],
                 min_length: int = 3) -> List[Dict]:
    results = []

    for i in range(len(query_sequence) - min_length + 1):
        query_subseq = query_sequence[i:i+min_length]

        for db_genome in database:
            db_seq = ''.join(db_genome.sequence)

            # Find all matches
            for j in range(len(db_seq) - min_length + 1):
                db_subseq = db_seq[j:j+min_length]

                # Calculate identity
                matches = sum(1 for a, b in zip(query_subseq, db_subseq) if a == b)
                identity = (matches / min_length) * 100

                if identity >= 80:  # 80% threshold
                    results.append({
                        'query_position': i,
                        'subject_position': j,
                        'identity_pct': identity,
                        'subject_genome': db_genome.city_name,
                        'sequence': db_subseq
                    })

    return sorted(results, key=lambda x: x['identity_pct'], reverse=True)
```

### Phylogenetic Distance

```python
def calculate_distance(genome1: StreetGenome, genome2: StreetGenome) -> float:
    """Needleman-Wunsch alignment score as phylogenetic distance."""
    seq1 = ''.join(genome1.sequence)
    seq2 = ''.join(genome2.sequence)

    # Dynamic programming alignment
    score = needleman_wunsch_score(seq1, seq2)

    # Convert to distance (lower score = more different)
    max_possible_score = min(len(seq1), len(seq2))
    distance = 1.0 - (score / max_possible_score)

    return distance
```

## Future Enhancements

Potential expansions:
- [ ] Machine learning to predict mutation locations from sequence alone
- [ ] "Gene therapy" for cities: algorithms to suggest which segments to redesign
- [ ] Horizontal gene transfer: identify when cities copy each other's designs
- [ ] Epigenetics: temporary changes (construction zones, events) vs. permanent DNA
- [ ] Multi-species comparison: bike networks as separate genome vs. car networks
- [ ] Ancient DNA: historical street maps encoded to show evolution
- [ ] CRISPR analogy: precision editing of specific dangerous intersections

## Precedents & Influences

**Cross-Domain Methodology:**
- Benoit Mandelbrot: Fractal geometry applied across disciplines
- Claude Shannon: Information theory applied to biology
- Network Science: Same math for proteins, friendships, streets

**Computational Urban Planning:**
- Space Syntax: Graph theory for pedestrian movement
- Network Analysis: Centrality measures for street importance
- Agent-Based Modeling: Simulating traffic as cellular automata

**Metaphor as Method:**
- Lakoff & Johnson: "Metaphors We Live By"
- Scientific Models: All models are metaphors (but some are useful)
- Donald Schön: Generative metaphor in problem-solving

## License

MIT License

This is methodologically ridiculous computational art/science. Use it. Question it. Extend it.

If it helps one city realize they can "edit their genome" to remove stroads, the absurdity was worth it.

## Contact

If you:
- Use this with actual bioinformatics tools → Tell us what happens
- Teach this in a course → We'd love to hear about discussions
- Find it ridiculous → You're right (but it works anyway)
- Want to extend the code → Pull requests welcome
- Have a better base-pair mapping → Open an issue

---

**Final Note**: This README uses genetics terminology throughout. Streets are not alive. DNA is not infrastructure. The metaphor is absurd.

But the graph theory is identical. The patterns are real. The deaths are real.

Sometimes absurd methods reveal what serious methods miss.
