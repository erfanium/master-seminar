import heapq
from typing import List


class ClusterProfiler:
    def __init__(self, name: str, idx: List[int], k=20):
        self.name = name
        self.idx = set(idx)
        self.k = k
        self.topk = []
        self._counter = 0  # unique counter to break score ties

    def process_variant(self, variant):
        in_cluster = {"count": 0, "sum": 0}
        out_cluster = {"count": 0, "sum": 0}

        for index, genotype in enumerate(variant.genotypes):
            obj = in_cluster if index in self.idx else out_cluster
            obj["count"] += 1
            obj["sum"] += genotype[0] + genotype[1]

        # Avoid division by zero
        if in_cluster["count"] == 0 or out_cluster["count"] == 0:
            return

        in_cluster_af = (in_cluster["sum"] / in_cluster["count"]) / 2
        out_cluster_af = (out_cluster["sum"] / out_cluster["count"]) / 2
        af = (
            (in_cluster["sum"] + out_cluster["sum"])
            / (in_cluster["count"] + out_cluster["count"])
        ) / 2

        af_diff = abs(in_cluster_af - out_cluster_af)

        # Prepare record
        entry = {
            "variant": variant,
            "af": af,
            "in_cluster_af": in_cluster_af,
            "out_cluster_af": out_cluster_af,
            "af_diff": af_diff,
        }

        # Increment counter to avoid dict comparison if af_diffs tie
        self._counter += 1
        key = (af_diff, self._counter, entry)

        # Maintain top-k heap
        if len(self.topk) < self.k:
            heapq.heappush(self.topk, key)
        else:
            heapq.heappushpop(self.topk, key)

    def get_topk(self):
        """Return top-k variants sorted by descending score."""
        # Extract only the entry dicts, sort by score descending
        return [item[2] for item in sorted(self.topk, key=lambda x: x[0], reverse=True)]
