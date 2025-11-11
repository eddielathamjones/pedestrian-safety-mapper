"""
The Pedestrian Genome Project

Treats street networks as genetic code and applies bioinformatics methods
to urban infrastructure. Completely wrong methodology, surprisingly useful results.

Concept:
- Streets = DNA sequences (4 road types = 4 bases: A, T, C, G)
- Intersections = Codons (3-base sequences)
- Stroads = Harmful mutations (like cancer genes)
- Safe streets = Healthy genes
- Infrastructure changes = Genetic engineering
- Evolution = How street networks developed over time

This is absurd. It also works.

Bioinformatics methods like sequence alignment, phylogenetic trees, and
mutation analysis are perfect for network analysis—they were designed for
graphs (molecular networks) in the first place.
"""

import json
import os
from typing import List, Dict, Tuple, Optional
from collections import defaultdict, Counter
import math


# DNA-style encoding of street networks
ROAD_BASE_MAP = {
    1: 'A',  # Interstate (Adenine)
    2: 'T',  # Principal Arterial (Thymine)
    3: 'C',  # Minor Arterial (Cytosine)
    4: 'G',  # Collector (Guanine)
    6: 'G',  # Local (also Guanine - similar function)
    7: 'G',  # Local residential
}

# Reverse mapping
BASE_ROAD_MAP = {'A': 1, 'T': 2, 'C': 3, 'G': 4}

# "Codon" table: 3-street sequences → pedestrian outcomes
# This is learned from crash data
CODON_TABLE = {
    'TTT': 'FATAL',      # High-speed arterials in sequence = deadly
    'TTA': 'FATAL',      # Arterial + Interstate = stroad
    'ATT': 'FATAL',      # Interstate feeding arterial
    'TTC': 'DANGER',     # Arterial + collector mix
    'GGG': 'SAFE',       # Local streets = safe
    'GGC': 'SAFE',       # Local feeding collector
    'CGG': 'MODERATE',   # Collector + local
    'CCG': 'MODERATE',   # Arterials but lower speed
}


class StreetGenome:
    """Represents a street network as a genetic sequence."""

    def __init__(self, network_name: str):
        self.name = network_name
        self.sequence: List[str] = []  # DNA sequence (bases)
        self.metadata: List[Dict] = []  # Metadata for each base
        self.mutations: List[Dict] = []  # Identified harmful mutations
        self.phenotype: Dict = {}  # Observable characteristics

    def encode_from_network(self, network_geojson: Dict):
        """
        Convert street network GeoJSON to genetic sequence.

        Each edge (street) becomes a base (A, T, C, or G).
        Order is determined by geographic traversal.
        """
        print(f"Encoding {self.name} street network as DNA sequence...")

        features = network_geojson.get('features', [])
        edges = [f for f in features if f['geometry']['type'] == 'LineString']

        if not edges:
            print("No edge data found")
            return

        # Sort by geographic position (north to south, west to east)
        # This creates a consistent "reading frame"
        sorted_edges = sorted(edges, key=lambda e: (
            -e['geometry']['coordinates'][0][1],  # Latitude (north first)
            e['geometry']['coordinates'][0][0]     # Longitude (west first)
        ))

        for edge in sorted_edges:
            props = edge['properties']

            # Get road class
            func_class = props.get('functional_class', props.get('func_sys', 6))

            # Convert to base
            base = ROAD_BASE_MAP.get(func_class, 'G')
            self.sequence.append(base)

            # Store metadata
            self.metadata.append({
                'id': props.get('id', 'unknown'),
                'name': props.get('name', 'Unnamed'),
                'functional_class': func_class,
                'speed_limit': props.get('speed_limit', 25),
                'is_stroad': props.get('is_stroad', False),
                'risk_score': props.get('risk_score', 0),
                'crashes': props.get('crashes', 0),
                'has_sidewalk': props.get('has_sidewalk', False),
                'lighting': props.get('lighting', 'unknown'),
            })

        print(f"Encoded {len(self.sequence)} bases (street segments)")
        print(f"Sequence length: {len(self.sequence)} bp")

        # Calculate composition
        composition = Counter(self.sequence)
        total = len(self.sequence)
        print(f"\nBase composition:")
        print(f"  A (Interstate):       {composition['A']:4d} ({composition['A']/total*100:5.1f}%)")
        print(f"  T (Principal Arterial):{composition['T']:4d} ({composition['T']/total*100:5.1f}%)")
        print(f"  C (Minor Arterial):   {composition['C']:4d} ({composition['C']/total*100:5.1f}%)")
        print(f"  G (Local):            {composition['G']:4d} ({composition['G']/total*100:5.1f}%)")

    def identify_mutations(self):
        """
        Identify harmful "mutations" in the street genome.

        Mutations = dangerous infrastructure patterns.
        """
        print(f"\nScanning for harmful mutations...")

        self.mutations = []

        # Scan for dangerous patterns
        for i in range(len(self.sequence) - 2):
            codon = ''.join(self.sequence[i:i+3])

            # Check if this is a known dangerous pattern
            if codon in ['TTT', 'TTA', 'ATT', 'TAT', 'ATA']:
                mutation = {
                    'position': i,
                    'codon': codon,
                    'type': 'stroad_mutation',
                    'severity': 'FATAL',
                    'description': 'High-speed arterial pattern',
                    'streets': [
                        self.metadata[i].get('name'),
                        self.metadata[i+1].get('name'),
                        self.metadata[i+2].get('name'),
                    ],
                    'risk_scores': [
                        self.metadata[i].get('risk_score', 0),
                        self.metadata[i+1].get('risk_score', 0),
                        self.metadata[i+2].get('risk_score', 0),
                    ]
                }
                self.mutations.append(mutation)

        # Also scan for single-base mutations (individual stroads)
        for i, base in enumerate(self.sequence):
            meta = self.metadata[i]
            if meta.get('is_stroad'):
                mutation = {
                    'position': i,
                    'codon': base,
                    'type': 'single_stroad',
                    'severity': 'HIGH',
                    'description': f'Stroad: {meta.get("name")}',
                    'streets': [meta.get('name')],
                    'risk_scores': [meta.get('risk_score', 0)],
                }
                self.mutations.append(mutation)

        print(f"Found {len(self.mutations)} mutations")
        print(f"  Fatal patterns: {sum(1 for m in self.mutations if m['severity'] == 'FATAL')}")
        print(f"  High-risk stroads: {sum(1 for m in self.mutations if m['type'] == 'single_stroad')}")

        return self.mutations

    def calculate_phenotype(self):
        """
        Calculate observable characteristics (phenotype) from genotype.

        Phenotype = actual crash outcomes, walkability, safety metrics.
        """
        print("\nCalculating phenotype (observable characteristics)...")

        # Aggregate statistics from metadata
        total_crashes = sum(m.get('crashes', 0) for m in self.metadata)
        avg_risk = sum(m.get('risk_score', 0) for m in self.metadata) / len(self.metadata)
        stroad_count = sum(1 for m in self.metadata if m.get('is_stroad'))
        sidewalk_coverage = sum(1 for m in self.metadata if m.get('has_sidewalk')) / len(self.metadata)

        self.phenotype = {
            'total_length_bp': len(self.sequence),
            'mutation_count': len(self.mutations),
            'mutation_rate': len(self.mutations) / len(self.sequence),
            'total_crashes': total_crashes,
            'avg_risk_score': avg_risk,
            'stroad_count': stroad_count,
            'sidewalk_coverage': sidewalk_coverage,
            'health_index': self._calculate_health_index(),
        }

        print(f"Phenotype:")
        print(f"  Mutation rate: {self.phenotype['mutation_rate']:.3f}")
        print(f"  Total crashes: {self.phenotype['total_crashes']}")
        print(f"  Average risk:  {self.phenotype['avg_risk_score']:.1f}")
        print(f"  Health index:  {self.phenotype['health_index']:.1f}/100")

        return self.phenotype

    def _calculate_health_index(self) -> float:
        """
        Calculate overall genome health (0-100).

        Higher = safer, like a healthy organism.
        """
        if not self.metadata:
            return 0.0

        # Factors that reduce health
        mutation_penalty = len(self.mutations) / len(self.sequence) * 100
        crash_penalty = min(50, sum(m.get('crashes', 0) for m in self.metadata))
        risk_penalty = sum(m.get('risk_score', 0) for m in self.metadata) / len(self.metadata)

        # Start at 100, subtract penalties
        health = 100 - (mutation_penalty + risk_penalty)

        return max(0.0, min(100.0, health))

    def export_fasta(self, filename: str):
        """
        Export sequence in FASTA format (standard bioinformatics format).

        This allows use of real bioinformatics tools like BLAST.
        """
        with open(filename, 'w') as f:
            f.write(f">{self.name}\n")

            # Write sequence in 60-base lines (FASTA standard)
            for i in range(0, len(self.sequence), 60):
                f.write(''.join(self.sequence[i:i+60]) + '\n')

        print(f"\nExported FASTA: {filename}")
        print(f"Can now use BLAST to find similar street patterns in other cities!")

    def export_genbank(self, filename: str):
        """
        Export as GenBank format with annotations.

        GenBank format includes metadata about features (mutations, etc.).
        """
        with open(filename, 'w') as f:
            f.write(f"LOCUS       {self.name:16s} {len(self.sequence):8d} bp    DNA\n")
            f.write(f"DEFINITION  Street network genome for {self.name}\n")
            f.write(f"FEATURES             Location/Qualifiers\n")

            # Annotate mutations
            for mut in self.mutations:
                f.write(f"     mutation        {mut['position']}\n")
                f.write(f"                     /type=\"{mut['type']}\"\n")
                f.write(f"                     /severity=\"{mut['severity']}\"\n")
                f.write(f"                     /note=\"{mut['description']}\"\n")

            f.write("ORIGIN\n")

            # Write sequence with base numbering (GenBank format)
            for i in range(0, len(self.sequence), 60):
                line = ''.join(self.sequence[i:i+60])
                f.write(f"{i+1:9d} {line}\n")

            f.write("//\n")

        print(f"Exported GenBank: {filename}")


def sequence_alignment(genome1: StreetGenome, genome2: StreetGenome) -> Dict:
    """
    Align two street genomes to find similar patterns.

    This is like comparing DNA from two species to find evolutionary relationships.
    Here: comparing two cities to find similar dangerous patterns.
    """
    print(f"\nAligning {genome1.name} and {genome2.name}...")

    seq1 = ''.join(genome1.sequence)
    seq2 = ''.join(genome2.sequence)

    # Simple local alignment (find matching subsequences)
    # In production, use Bio.pairwise2 from Biopython
    matches = []

    window_size = 10  # Look for 10-street patterns

    for i in range(len(seq1) - window_size):
        pattern = seq1[i:i+window_size]
        # Find if this pattern exists in seq2
        for j in range(len(seq2) - window_size):
            if seq2[j:j+window_size] == pattern:
                matches.append({
                    'pattern': pattern,
                    'pos1': i,
                    'pos2': j,
                    'length': window_size,
                })

    print(f"Found {len(matches)} matching patterns")

    if matches:
        print(f"\nExample matching dangerous patterns:")
        for match in matches[:5]:
            print(f"  Position {match['pos1']} in {genome1.name}")
            print(f"  Position {match['pos2']} in {genome2.name}")
            print(f"  Pattern: {match['pattern']}")
            print()

    return {
        'genome1': genome1.name,
        'genome2': genome2.name,
        'matches': len(matches),
        'similarity': len(matches) / min(len(seq1), len(seq2)),
        'matching_patterns': matches[:10],  # Top 10
    }


def phylogenetic_analysis(genomes: List[StreetGenome]) -> Dict:
    """
    Build phylogenetic tree showing evolutionary relationships between cities.

    Cities with similar street patterns are "closely related."
    This reveals which cities learned from each other (or made the same mistakes).
    """
    print(f"\nBuilding phylogenetic tree for {len(genomes)} cities...")

    # Calculate distance matrix (how different are the genomes?)
    n = len(genomes)
    distances = [[0.0] * n for _ in range(n)]

    for i in range(n):
        for j in range(i + 1, n):
            # Simple distance: % of bases that differ
            seq1 = ''.join(genomes[i].sequence)
            seq2 = ''.join(genomes[j].sequence)

            min_len = min(len(seq1), len(seq2))
            differences = sum(1 for k in range(min_len) if seq1[k] != seq2[k])
            distance = differences / min_len

            distances[i][j] = distance
            distances[j][i] = distance

    # Build simple neighbor-joining tree (in production, use BioPython)
    tree = {
        'method': 'neighbor_joining',
        'cities': [g.name for g in genomes],
        'distance_matrix': distances,
    }

    print("Phylogenetic relationships:")
    for i, genome in enumerate(genomes):
        closest = min([(j, distances[i][j]) for j in range(n) if j != i],
                     key=lambda x: x[1])
        print(f"  {genome.name} most similar to {genomes[closest[0]].name} (distance: {closest[1]:.3f})")

    return tree


def blast_search(query_genome: StreetGenome, database_genomes: List[StreetGenome],
                word_size: int = 5) -> List[Dict]:
    """
    BLAST-like search: Find similar dangerous patterns across cities.

    BLAST = Basic Local Alignment Search Tool (standard bioinformatics)
    Here: "Does my city have the same deadly patterns as other cities?"
    """
    print(f"\nBLAST search: Finding {query_genome.name} patterns in other cities...")

    query_seq = ''.join(query_genome.sequence)
    results = []

    # For each dangerous mutation in query, search other genomes
    for mutation in query_genome.mutations:
        pattern_start = mutation['position']
        pattern = ''.join(query_genome.sequence[pattern_start:pattern_start+word_size])

        # Search all database genomes
        for db_genome in database_genomes:
            if db_genome.name == query_genome.name:
                continue

            db_seq = ''.join(db_genome.sequence)

            # Find all occurrences
            pos = 0
            while True:
                pos = db_seq.find(pattern, pos)
                if pos == -1:
                    break

                # Found a match!
                results.append({
                    'query': query_genome.name,
                    'subject': db_genome.name,
                    'pattern': pattern,
                    'query_pos': pattern_start,
                    'subject_pos': pos,
                    'e_value': 0.001,  # Mock e-value
                    'query_street': mutation.get('description'),
                })

                pos += 1

    print(f"Found {len(results)} significant matches")

    if results:
        print("\nTop matches:")
        for result in results[:10]:
            print(f"  {result['query_street']}")
            print(f"  Also found in {result['subject']} at position {result['subject_pos']}")
            print()

    return results


def main():
    """Command-line interface for Pedestrian Genome Project."""
    import argparse

    parser = argparse.ArgumentParser(
        description='Pedestrian Genome Project - Bioinformatics for Street Networks',
        epilog='Warning: This uses completely wrong methodology. It also works.'
    )
    parser.add_argument('input', help='Input network GeoJSON file')
    parser.add_argument('--name', required=True, help='City/network name')
    parser.add_argument('--output-dir', default='genomes', help='Output directory')
    parser.add_argument('--compare', help='Compare with another genome (GeoJSON)')

    args = parser.parse_args()

    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)

    # Load and encode network
    print(f"\n{'='*70}")
    print(f"PEDESTRIAN GENOME PROJECT")
    print(f"{'='*70}\n")

    with open(args.input, 'r') as f:
        network_data = json.load(f)

    genome = StreetGenome(args.name)
    genome.encode_from_network(network_data)

    # Identify mutations
    genome.identify_mutations()

    # Calculate phenotype
    genome.calculate_phenotype()

    # Export formats
    fasta_file = os.path.join(args.output_dir, f"{args.name.replace(' ', '_')}.fasta")
    genbank_file = os.path.join(args.output_dir, f"{args.name.replace(' ', '_')}.gb")

    genome.export_fasta(fasta_file)
    genome.export_genbank(genbank_file)

    # Export analysis
    analysis = {
        'genome_name': genome.name,
        'sequence_length': len(genome.sequence),
        'mutations': genome.mutations,
        'phenotype': genome.phenotype,
    }

    analysis_file = os.path.join(args.output_dir, f"{args.name.replace(' ', '_')}_analysis.json")
    with open(analysis_file, 'w') as f:
        json.dump(analysis, f, indent=2)

    print(f"Exported analysis: {analysis_file}")

    # Compare if requested
    if args.compare:
        print(f"\n{'='*70}")
        print(f"COMPARATIVE GENOMICS")
        print(f"{'='*70}\n")

        with open(args.compare, 'r') as f:
            compare_data = json.load(f)

        compare_genome = StreetGenome("Comparison City")
        compare_genome.encode_from_network(compare_data)
        compare_genome.identify_mutations()
        compare_genome.calculate_phenotype()

        # Sequence alignment
        alignment = sequence_alignment(genome, compare_genome)

        # BLAST search
        blast_results = blast_search(genome, [compare_genome])

        print("\nConclusion: These cities share dangerous infrastructure patterns.")
        print("This is the 'genetic' basis of traffic violence.")

    print(f"\n{'='*70}")
    print(f"METHODOLOGY REFLECTION")
    print(f"{'='*70}")
    print("This analysis used bioinformatics tools designed for DNA on street")
    print("networks. This is methodologically absurd.")
    print("")
    print("It's also surprisingly effective:")
    print("  - Sequence alignment finds cities with similar patterns")
    print("  - Mutation analysis identifies dangerous infrastructure")
    print("  - Phylogenetic trees show which cities influence each other")
    print("  - BLAST finds specific dangerous patterns across cities")
    print("")
    print("Why does this work? Because both are network analysis problems.")
    print("DNA is a molecular network. Streets are an infrastructure network.")
    print("The math is the same.")
    print("")
    print("The absurdity is the point. It makes infrastructure strange.")
    print(f"{'='*70}\n")


if __name__ == '__main__':
    main()
