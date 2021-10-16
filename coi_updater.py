def coi_updater(cluster_pops, cluster_sizes, totpop):
    def updater(partition):
        ideal_pop = totpop / len(partition)
        district_cluster_pops = [max(partition[cluster].values()) for cluster in cluster_pops]
        district_cluster_idealized = [x / ideal_pop for x in district_cluster_pops]
        district_cluster_normalized = [x / cluster_sizes[cluster] for x, cluster in zip(district_cluster_pops, cluster_pops)]

        # print(district_cluster_idealized)
        # print(district_cluster_normalized, sum(district_cluster_normalized))

        score = sum([1 for x, y in zip(district_cluster_idealized, district_cluster_normalized) if x > 0.75 or y > 0.75])
        print(score)
        return score

    return updater
